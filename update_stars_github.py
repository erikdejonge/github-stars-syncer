# coding=utf-8
"""
update script
"""

import sys
reload(sys)

# noinspection PyUnresolvedReferences


sys.setdefaultencoding("utf-8")

import tarfile
import json
import os
import pipes
import cPickle
from git import Repo
from os.path import join, expanduser, exists
from multiprocessing import Pool, cpu_count

import shutil

USERNAME = "erikdejonge"


def get_star_page(num):
    """
    @type num: int
    @return: None
    """
    cmd = 'curl -s "https://api.github.com/users/'+USERNAME+'/starred?per_page=100&page=' + str(num) + '" > j' + str(num) + '.json'
    print cmd,
    os.system(cmd)

    if os.path.exists("j" + str(num) + ".json"):
        parsed = json.load(open("j" + str(num) + ".json"))
        print len(parsed), "downloaded"
        os.remove("j" + str(num) + ".json")
        return parsed

    return []


def clone_or_pull_from(remote):
    """
    @type remote: str, unicode
    @return: None
    """
    name = pipes.quote(os.path.basename(remote).replace(".git", "")).strip()
    gp = join(join(join(expanduser("~"), "workspace"), "github"), name)

    if exists(gp):
        r = Repo(gp)
        r.remote().update()


        ret = name + " " + str(r.active_branch) + " pulled"
        print "\033[37m", ret, "\033[0m"
    else:
        ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"
        print "\033[32m", ret, "\033[0m"
        newrepos = join(join(join(expanduser("~"), "workspace"), "github"), "_newrepos")

        if not exists(newrepos):
            os.mkdir(newrepos)

        gp = join(newrepos, name)
        ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"
        print "\033[30m", ret, "\033[0m"

    return True


def main():
    """
    main
    """
    if not os.path.exists("starlist.pickle"):
        maxnum = 100
        lt = []

        for num in range(0, maxnum):
            stars = get_star_page(num + 1)

            if len(stars) == 0:
                break

            lt.extend(stars)

        cPickle.dump(lt, open("starlist.pickle", "w"))
    else:
        lt = cPickle.load(open("starlist.pickle"))

    githubdir = os.path.join(os.path.expanduser("~"), "workspace/github")
    print "\033[34mGithub folder:", githubdir, "\033[0m"
    newrepos = join(githubdir, "_newrepos")

    if exists(newrepos) and os.path.isdir(newrepos):
        shutil.rmtree(newrepos)

    names = [x["name"] for x in lt]
    d = {}
    double_found = False

    for n in names:
        if n in d:
            print "\033[91mdouble:", n, "\033[0m"
            double_found = True

        d[n] = True

    if double_found:
        raise AssertionError("found double name")

    ltdir = [x.strip().lower() for x in os.listdir(githubdir)]
    cnt = 0
    to_clone_or_pull = []
    ghbnames = []

    for i in lt:
        ghbnames.append(i["name"])
        cnt += 1
        to_clone_or_pull.append(i["git_url"])

    p = Pool(cpu_count() * 2)

    for retval in p.map(clone_or_pull_from, to_clone_or_pull):
        if not retval:
           raise AssertionError(retval)

    for folder in os.listdir(githubdir):
        found = False

        for ghbn in ghbnames:
            if ghbn == folder:
                found = True

        if not found:
            delp = join(githubdir, folder)

            if exists(delp):
                if os.path.isdir(delp):
                    if os.path.basename(delp) != "_newrepos":
                        print "\033[31m", "tarring:", delp, "\033[0m"
                        tar = tarfile.open(pipes.quote(os.path.basename(delp))+".tar", "w")
                        tar.add(delp)
                        tar.close()
                else:
                    print "\033[91m", "WARNING: files in directory", delp, "\033[0m"
            else:
                print "\033[91m", delp, "\033[0m"

    print "\033[32mDone\033[0m"
    if len(lt) != len(ltdir):
        print "\033[31mItems and folderitems is not equal\033[0m"
        print "\033[90m", len(lt), "items github", "\033[0m"
        print "\033[90m", len(ltdir), "items folder", "\033[0m"
        dirnames = os.listdir(githubdir)

        for ghbn in names:
            found = False

            for folder in dirnames:
                if ghbn == folder:
                    found = True

            if not found:
                print "\033[91m", ghbn, "\033[0m"

        for folder in dirnames:
            found = False

            for ghbn in names:
                if ghbn == folder:
                    found = True

            if not found:
                print "\033[91m", folder, "\033[0m"


if __name__ == "__main__":
    main()
