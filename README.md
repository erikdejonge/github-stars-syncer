# github-stars-syncer
Syncs a folder with the starred repos on github. 

All new repositories are cloned to workspace/github/, existing ones are pulled, and if they are on disk but not in starred the disk version will be deleted.

New repositories are also checked out in workspace/github/_newrepos. 

####Command
Github enforces a ratelimit on the anonymous api, for dev purposes the list is cached. To have a fresh copy first delete this cache.

```bash
cd ~/workspace
cd github-stars-syncer
rm starlist.pickle
```

####Alias
```bash
alias ghbstars="cd ~/workspace/github-stars-syncer&&rm starlist.pickle&&python update_stars_github.py"
```


