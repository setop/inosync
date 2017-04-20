# inosync

Author: [Setop](mailto:setop@fiveinthewood.com)

Version: 0.1.0

Web: http://github.com/setop/inosync

This is a fork of [hollow/inosync](https://github.com/hollow/inosync) which focuses on limiting the scope of synchronization performed after each modification of the source.

The initial version performs a rsync of the whole hierarchy `rsync --recursive /source remote:/destination` for each node. This is **not sustainable** when the hierarchy contains thousands of files and directories.

This version is going to perform a narrower synchronization, like : `rsync --include='modified' /source/path/to/parent/ remote:/destination/path/to/parent/`

# Rationale

System administrators have relied on cron+rsync for years to constantly synchronize files and directories to remote machines. However, this technique has a huge disadvantage for content distribution with near real-time requirements, like podcasts and blogging.

The inosync daemon leverages the inotify service available in recent Linux kernels to monitor and synchronize changes within directories to remote nodes. 

This forked version allows to deal with huge hierarchy of files and directories by narrowing the synchronization performed after each modification on the source. 

# Usage

```
  inosync [OPTIONS]

    -c FILE     load configuration from FILE
    -v          print debugging information
    --version   show program's version number and exit
    -h, --help  show this help message and exit
```

# Configuration

Configuration file is a simple python script, merely declaring necessary variables. Below is an example configuration to synchronize "/var/www" except ".bin" files to three remote locations:

```
  # directory that should be watched for changes
  wpath = "/var/www"

  # exclude list for inotify
  rexcludes = [
  	"*.bin",
  ]

  # rpaths has one-to-one correspondence with wpaths for syncing multiple directories
  rpath = "/var/www"

  # remote locations in rsync syntax, use "" for local
  rnodes = [
  	"user1@a.mirror.com:",
  	"user2@b.mirror.com:",
  	"user3@c.mirror.com:",
  ]

  # extra, raw parameters to rsync
  #extra = "--rsh=ssh -a"

  # limit remote sync speed (in KB/s, 0 = no limit)
  #rspeed = 0

  # rsync binary path
  #rsync = "/usr/bin/rsync"
```

# Limitations

Compare to initial version, there are some limitations due to simplification of code: 

* "pretend" option has been remove. This can be easily worked around by customizing the "rsync" command, in the configuration file (see sample configuration file)
* "deamonize" option has been removed. This can be easily worked around by invoking the script in conjunction with `nohup <command> &`
* "edelay" (aka: event delay) option has been removed. As synchronization only acts on a minimal set of files, there is no point waiting between events.
* "emask" (aka: event mask) option has been removed. For the synchronization to be consistent, event types must be chosen by the script not by the user.
* "wpaths" (watched paths) and "rpaths" (aka remote paths) have been replaced by single valued "wpath" and "rpath". This simplifies the script as we don't need to keep a mapping between a local path and a remote path. This can be easily worked around by invoking inosync on each pair of wpath/rpath.

# Benefits over original version

Compare to initial version, there are big benefits due to rethink of behavior:

* exclusions are given to inotify, not rsync. This allow to reduce number of watched items.
* only modifications are synced, not the whole hierarchy. This leads to an acceptable synchronization duration.

# Requirements

To use this script you need the following software installed on your system:

* Linux-2.6.13 or later
* Python-2.5 or later
* [Pyinotify](https://pypi.python.org/pypi/pyinotify)-0.8.7 or later

This version has been test under Linux 4.4.0, with pyinotify-0.9.6.


# Issues 

## no space left on device

Linux opens one watch per file and per directory in the source hierarchy. The limitation for a standard user is usually 8192. Use `cat /proc/sys/fs/inotify/max_user_watches` to know the limit on your system.

If this limit is to low, it can be changed by root, using `sudo sysctl fs.inotify.max_user_watches=12345`

## move or rename – aka `mv` command – fails

Currently, inosync does not handle moves due to a limitation of rsync. There is no way to tell rsync a move has happened.

### On files

When moving a file, this result in re-transferring data where it could be avoided. Move events on files are performed as a delete action and create action.

### On directories

This could result on data loss on the remote nodes when moving a directory (like `mv source/a/b source/a/c`). On remote host, the "from directory" is removed with its content and the "to directory" is created but not its content. That is why move event on directories are logged but **no action is performed**.


# Related Software

inosync is similar to [lsyncd] (http://www.pri.univie.ac.at/index.php?c=show&CEWebS_what=Lsyncd).

A comparison to other approaches like DRBD, incron and FUSE can be found at lsyncds project page, mentioned above.