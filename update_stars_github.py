#!/usr/bin/env python3
# coding=utf-8
"""
update script
"""
from __future__ import division, print_function, absolute_import, unicode_literals
from future import standard_library

import os
import sys
import json
import pipes
import pickle
import shutil
import tarfile
import multiprocessing

from git import Repo
from threading import Lock
from consoleprinter import console_exception
from multiprocessing.dummy import Pool
from os.path import join, exists, dirname, expanduser

USERNAME = "<<username>>"

dotlock = Lock()
dotprinted = False


def clone_or_pull_from(remote, name):
    """
    @type remote: str, unicode
    @type name: str, unicode
    @return: None
    """
    cnt = 0
    global dotprinted
    global dotlock

    while True:
        try:
            gp = join(join(join(expanduser("~"), "workspace"), "github"), name)

            if exists(gp):
                r = Repo(gp)
                origin = r.remote()
                origin.fetch()
                origin.pull()

                try:
                    dotlock.acquire()

                    if dotprinted is True:
                        sys.stdout.write("\033[30m.\033[0m")

                    sys.stdout.flush()
                    dotprinted = True
                finally:
                    dotlock.release()

                # ret = name + " " + str(r.active_branch) + " pulled"
            else:
                newrepos = join(join(join(expanduser("~"), "workspace"), "github"), os.path.dirname(name))

                if not exists(newrepos):
                    os.mkdir(newrepos)

                newrepos = join(join(join(expanduser("~"), "workspace"), "github"), name)

                if not exists(newrepos):
                    os.mkdir(newrepos)

                ret = name + " " + str(Repo.clone_from(remote, newrepos).active_branch) + " cloned"
                try:
                    dotlock.acquire()

                    if dotprinted is True:
                        dotprinted = True
                        ret = "\n" + ret
                finally:
                    dotlock.release()

                print("\033[32m" + ret + "\033[0m")
                newreposlink = join(join(join(expanduser("~"), "workspace"), "github"), "_newrepos")

                if not exists(newreposlink):
                    os.mkdir(newreposlink)

                newreposlink = join(newreposlink, os.path.dirname(name))

                if not exists(newreposlink):
                    os.mkdir(newreposlink)

                newreposlinksym = newreposlink + "/" + os.path.basename(name)
                os.system("ln -s " + newrepos + " " + newreposlinksym)
        except Exception as e:
            console_exception(e)
            cnt += 1

            if cnt > 3:
                break
        finally:
            break

    return True


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


def main():
    """
    main
    """
    get_stars = True
    if get_stars:
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

    p = Pool(multiprocessing.cpu_count() * 3)
    debug = False

    if debug:
        for arg in to_clone_or_pull:
            start_clone_or_pull(arg)
    else:
        for retval in p.map(start_clone_or_pull, to_clone_or_pull):
            if not retval:
                print(retval)

    needsenter = True

    for motherf in os.listdir(githubdir):
        if os.path.isdir(join(githubdir, motherf)):
            for folder in os.listdir(join(githubdir, motherf)):
                found = False

                for ghbn in ghbnames:
                    if ghbn == join(motherf, folder):
                        found = True

                if not found:
                    delp = join(join(githubdir, motherf), folder)

                    if exists(delp) and "_projects" not in delp:
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

                                if os.path.islink(delp):
                                    os.remove(delp)
                                else:
                                    shutil.rmtree(delp)


                        else:
                            print("\033[91m", "WARNING: files in directory", delp, "\033[0m")
                    else:
                        if os.path.islink(delp) or ".DS_Store" in delp:
                            if os.path.islink(delp):
                                os.remove(delp)
                            sys.stdout.write("\033[30m*\033[0m")
                            sys.stdout.flush()
                            needsenter = True
                        else:
                            if needsenter:
                                print()

                            print("\033[91mnot found:", delp, "\033[0m")
                            needsenter = False

    print()

    for root, dirs, files in os.walk(githubdir):
        for namefolder in dirs:
            namefolderpath = os.path.join(root, namefolder)

            if len(os.listdir(namefolderpath)) == 0 and ".git" not in namefolderpath and namefolderpath.count("/") <= 6:
                print("\033[31mEmptyfolder del:", os.path.join(root, namefolder), "\033[0m")
                shutil.rmtree(os.path.join(root, namefolder))

    print("\033[32mDone\033[0m")
    fp = open(join(githubdir, "list.txt"), "wt")

    for i in lt:
        fp.write(join(githubdir, i["full_name"]) + "\n")


def start_clone_or_pull(args):
    """
    @type args: tuple
    @return: None
    """
    url, name = args
    return clone_or_pull_from(url, name)

standard_library.install_aliases()


if __name__ == "__main__":
    main()
