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
from consoleprinter import console_exception
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
    cnt = 0

    while True:
        try:
            gp = join(join(join(expanduser("~"), "workspace"), "github"), name)

            if exists(gp):
                # r = Repo(gp)
                # origin = r.remote()
                # origin.fetch()
                # origin.pull()
                # ret = name + " " + str(r.active_branch) + " pulled"
                # print "\033[37m", ret, "\033[0m"
                sys.stdout.write("\033[37m.\033[0m")
                sys.stdout.flush()
            else:
                # ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"
                # print "\033[32m", ret, "\033[0m"
                newrepos = join(join(join(expanduser("~"), "workspace"), "github"), name)

                if not exists(newrepos):
                    os.mkdir(newrepos)

                ret = name + " " + str(Repo.clone_from(remote, newrepos).active_branch) + " cloned"
                print("\033[32m", ret, "\033[0m")
                newreposlink = join(join(join(expanduser("~"), "workspace"), "github"), "_newrepos")

                if not exists(newreposlink):
                    os.mkdir(newreposlink)

                if not os.path.exists(newreposlink+"/"+os.path.basename(os.path.dirname(newrepos))):
                    os.mkdir(newreposlink+"/"+os.path.dirname(newrepos))
                os.system("ln -s " + newrepos + " " + newreposlink+"/"+os.path.basename(os.path.dirname(newrepos)))
        except Exception as e:
            print(e)
            cnt += 1

            if cnt > 3:
                break
        finally:
            break

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

        pickle.dump(lt, open("starlist.pickle", "wb"))
    else:
        lt = pickle.load(open("starlist.pickle", "rb"))

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

    cnt = 0
    to_clone_or_pull = []
    ghbnames = []

    for i in lt:
        name = i["full_name"]
        ghbnames.append(name)
        cnt += 1
        to_clone_or_pull.append((i["git_url"], name))

    p = Pool(cpu_count() * 2)

    # debug = False
    # if debug:
    #     for arg, name in to_clone_or_pull:
    #         start_clone_or_pull(arg)
    for retval in p.map(start_clone_or_pull, to_clone_or_pull):
        if not retval:
            print(retval)

    for motherf in os.listdir(githubdir):
        if os.path.isdir(join(githubdir, motherf)):
            for folder in os.listdir(join(githubdir, motherf)):
                found = False

                for ghbn in ghbnames:
                    if ghbn == join(motherf, folder):
                        found = True

                if not found:
                    delp = join(join(githubdir, motherf), folder)

                    if exists(delp):
                        if os.path.isdir(delp):
                            if "_newrepos" not in delp:
                                print("\n\033[31m", "backup and delete:", delp, "\033[0m")
                                bupf = join(join(expanduser("~"), "workspace"), "backup")

                                if not exists(bupf):
                                    os.mkdir(bupf)

                                bupf = join(join(expanduser("~"), "workspace"), "backup")

                                if not exists(bupf):
                                    os.mkdir(bupf)

                                bupf = join(bupf, "github")

                                if not exists(bupf):
                                    os.mkdir(bupf)

                                bupf = join(bupf, motherf)

                                if not exists(bupf):
                                    os.mkdir(bupf)

                                tarname = join(bupf, pipes.quote(os.path.basename(delp)) + ".tar.gz")
                                print(tarname)
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
                                shutil.rmtree(join(githubdir, motherf))
                        else:
                            print("\033[91m", "WARNING: files in directory", delp, "\033[0m")
                    else:
                        print("\033[91m", delp, "\033[0m")

    print("\n\033[32mDone\033[0m")
    fp = open(join(githubdir, "list.txt"), "wt")

    for i in lt:
        fp.write(join(githubdir, i["full_name"]) + "\n")


if __name__ == "__main__":
    main()
