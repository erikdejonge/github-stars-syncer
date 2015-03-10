# coding=utf-8
"""
update script
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
import sys
import tarfile
import json
import os
import pipes
import pickle
from git import Repo
from os.path import join, expanduser, exists, dirname
from multiprocessing import Pool, cpu_count

import shutil

USERNAME = "<<username>>"


def get_star_page(num):
    """
    @type num: int
    @return: None
    """
    global USERNAME
    if USERNAME == "<<username>>":
        if os.path.exists("username.conf"):
            USERNAME = open("username.conf").read().strip()
        else:
            raise AssertionError("USERNAME: not set (line 23)")

    cmd = 'curl -s "https://api.github.com/users/' + USERNAME + '/starred?per_page=100&page=' + str(num) + '" > j' + str(num) + '.json'
    print(cmd, end=' ')
    os.system(cmd)

    if os.path.exists("j" + str(num) + ".json"):
        parsed = json.load(open("j" + str(num) + ".json"))
        print(len(parsed), "downloaded")
        os.remove("j" + str(num) + ".json")
        return parsed

    return []


def clone_or_pull_from(remote, name):
    """
    @type remote: str, unicode
    @type name: str, unicode
    @return: None
    """
    gp = join(join(join(expanduser("~"), "workspace"), "github"), name)

    if exists(gp):
        r = Repo(gp)
        origin = r.remote()
        origin.fetch()
        origin.pull()
        ret = name + " " + str(r.active_branch) + " pulled"
        #print "\033[37m", ret, "\033[0m"
        sys.stdout.write("\033[37m.\033[0m")
        sys.stdout.flush()
    else:
        ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"
        #print "\033[32m", ret, "\033[0m"
        newrepos = join(join(join(expanduser("~"), "workspace"), "github"), "_newrepos")

        if not exists(newrepos):
            os.mkdir(newrepos)

        gp = join(newrepos, name)
        ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"
        print("\n\033[32m", ret, "\033[0m")

    return True


def start_clone_or_pull(args):
    """
    @type args: tuple
    @return: None
    """
    url, name = args
    return clone_or_pull_from(url, name)


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

        pickle.dump(lt, open("starlist.pickle", "w"))
    else:
        lt = pickle.load(open("starlist.pickle"))

    githubdir = os.path.join(os.path.expanduser("~"), "workspace/github")
    print("\033[34mGithub folder:", githubdir, "\033[0m")
    newrepos = join(githubdir, "_newrepos")

    if exists(newrepos) and os.path.isdir(newrepos):
        shutil.rmtree(newrepos)

    names = [x["name"] for x in lt]
    d = {}
    doubles_found = []
    
    for n in names:
        if n in d:
            doubles_found.append(n)

        d[n] = True

    ltdir = [x.strip().lower() for x in os.listdir(githubdir)]
    cnt = 0
    to_clone_or_pull = []
    ghbnames = []
    doublecheckname = []
    for i in lt:
        if i["name"] not in doubles_found:
            name = i["name"]
            ghbnames.append(name)
        else:
            doubles_found.remove(i["name"])
            
            name = i["full_name"].replace("/", "_")
            if name not in ltdir:
                print("\033[95mdouble:", i["name"], "->", name, "\033[0m")
            doublecheckname.append(name)
            ghbnames.append(name)

        cnt += 1
        to_clone_or_pull.append((i["git_url"], name))

    p = Pool(cpu_count() * 2)
    debug = False

    if debug:
        for arg, name in to_clone_or_pull:
            start_clone_or_pull(arg)
    else:
        for retval in p.map(start_clone_or_pull, to_clone_or_pull):
            if not retval:
                print(retval)

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
                        print("\n\033[31m", "backup and delete:", delp, "\033[0m")
                        bupf = join(join(expanduser("~"), "workspace"), "backup")

                        if not exists(bupf):
                            os.mkdir(bupf)

                        bupf = join(bupf, "github")

                        if not exists(bupf):
                            os.mkdir(bupf)

                        tarname = join(bupf, pipes.quote(os.path.basename(delp)) + ".tar.gz")
                        tar = tarfile.open(tarname, "w:gz")

                        def modify(ti):
                            """
                            @type ti: str, unicode
                            @return: None
                            """
                            ti.name = ti.name.replace(dirname(delp).lstrip("/"), "")
                            return ti

                        tar.add(delp, filter=modify)
                        tar.close()
                        shutil.rmtree(delp)
                else:
                    print("\033[91m", "WARNING: files in directory", delp, "\033[0m")
            else:
                print("\033[91m", delp, "\033[0m")

    print("\n\033[32mDone\033[0m")
    if len(lt) != len(ltdir):
        dirnames = os.listdir(githubdir)
        showmessage = False

        for ghbn in names:
            found = False

            for folder in dirnames:
                if ghbn == folder:
                    found = True
                    showmessage = True

            if not found:
                print("\033[31m", ghbn, "diff with gh\033[0m")

        for folder in dirnames:
            if folder != "_newrepos":
                found = False

                for ghbn in names:
                    if ghbn == folder:
                        found = True
                        showmessage = True

                if not found:
                    if folder not in doublecheckname:
                        print("\033[34m", folder, "diff with dir\033[0m")

        if showmessage:
            #print "\033[31mItems and folderitems is not equal\033[0m"
            print("\033[90m", len(lt), "items github", "\033[0m")
            print("\033[90m", len(ltdir), "items folder", "\033[0m")


if __name__ == "__main__":
    main()
