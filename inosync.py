#!/usr/bin/env python2

from optparse import OptionParser, make_option
from syslog import *
from pyinotify import *

__author__ = "setop"
__copyright__ = "Copyright (c) 2017 Setop <setop@github.com>"
__version__ = 0, 1, 0

OPTION_LIST = [
    make_option(
        "-c", dest="config",
        default="/etc/inosync/default.py",
        metavar="FILE",
        help="load configuration from FILE"),
    make_option(
        "-v", dest="verbose",
        action="store_true",
        default=False,
        help="print debugging information"),
]

DEFAULT_EVENTS = [
    "IN_CLOSE_WRITE",
    "IN_CREATE",
    "IN_DELETE",
    "IN_MOVED_FROM",
    "IN_MOVED_TO",
]


class RsyncEvent(ProcessEvent):

    #def __init__(self):
    #    pass # prevent call to parent

    def sync(self, src, dst, include):
        """
        build cmd and run process for each node
        :param src: source parent directory
        :param dst: destination parent directory
        :param include: file or directory changed
        :return: None
        """
        args = [config.rsync, "-ltp", "--dirs", "--delete"]
        if config.extra:
            args.append(config.extra)
        if int(config.rspeed) > 0:
            args.append("--bwlimit=%s" % config.rspeed)
        if config.logfile:
            args.append("--log-file=%s" % config.logfile)
        args.append("--include='%s'" % include)
        args.append(src + '/')
        args.append("%s" + dst + '/')  # to set node:dst in the nodes loop
        cmd = " ".join(args)
        for node in config.rnodes:
            ncmd = cmd % node  # set node:dst
            syslog(LOG_DEBUG, "executing %s" % ncmd)
            process = os.popen(ncmd)
            for line in process:
                syslog(LOG_DEBUG, "[rsync] %s" % line.strip())

    def process_default(self, event):
        # IMPROVE create event on regular files could be ignored as a write event is going to occur,
        # but it must be kept for symlink for example
        syslog(LOG_DEBUG, `event`)
        if (event.mask & 0x00008000) > 0: # IN_IGNORED, which should have been filtered
            syslog(LOG_DEBUG, "IN_IGNORED")
            return
        src = event.path
        dst = config.rpath + src[len(config.wpath):]
        if event.dir and (event.mask & (0x00000040|0x00000080))>0: # IN_MOVE_FROM or IN_MOVE_TO on IS_DIR
            # mask=0x40000040 maskname=IN_MOVED_FROM|IN_ISDIR
            # mask=0x40000080 maskname=IN_MOVED_TO|IN_ISDIR
            syslog(LOG_WARNING, "must ignore "+`event`)
        else:
            self.sync(src, dst, event.name)


def load_config(filename):
    if not os.path.isfile(filename):
        raise RuntimeError, "Configuration file does not exist: %s" % filename

    configdir = os.path.dirname(filename)
    configfile = os.path.basename(filename)

    if configfile.endswith(".py"):
        configfile = configfile[0:-3]
    else:
        raise RuntimeError, "Configuration file must be a importable python file ending in .py"

    sys.path.append(configdir)
    exec ("import %s as __config__" % configfile)
    sys.path.remove(configdir)

    global config
    config = __config__

    if not "wpath" in dir(config):
        raise RuntimeError, "no paths given to watch"

    if not "rpath" in dir(config):
        raise RuntimeError, "no paths given for the transfer"

    if not "rnodes" in dir(config) or len(config.rnodes) < 1:
        raise RuntimeError, "no remote nodes given"

    if not "rspeed" in dir(config) or config.rspeed < 0:
        config.rspeed = 0

    if not "logfile" in dir(config):
        config.logfile = None

    if not "extra" in dir(config):
        config.extra = ""
    if not "rsync" in dir(config):
        config.rsync = "/usr/bin/rsync"
    if not os.path.isabs(config.rsync):
        raise RuntimeError, "rsync path needs to be absolute"
    if not os.path.isfile(config.rsync):
        raise RuntimeError, "rsync binary does not exist: %s" % config.rsync


def main():
    parser = OptionParser(option_list=OPTION_LIST, version="%prog " + ".".join(map(str, __version__)))
    (options, args) = parser.parse_args()

    if len(args) > 0:
        parser.error("too many arguments")

    logopt = LOG_PID | LOG_CONS | LOG_PERROR
    openlog("inosync", logopt, LOG_DAEMON)
    if options.verbose:
        setlogmask(LOG_UPTO(LOG_DEBUG))
    else:
        setlogmask(LOG_UPTO(LOG_INFO))

    load_config(options.config)

    syslog(LOG_DEBUG, "source " + config.wpath)
    syslog(LOG_DEBUG, "destination " + config.rpath)
    import fnmatch
    wm = WatchManager(exclude_filter=ExcludeFilter(map(fnmatch.translate, config.rexcludes)))
    ev = RsyncEvent()
    AsyncNotifier(wm, ev)
    mask = reduce(lambda x, y: x | y, [EventsCodes.ALL_FLAGS[e] for e in DEFAULT_EVENTS])
    wm.add_watch(config.wpath, mask, rec=True, auto_add=True)
    asyncore.loop()
    sys.exit(0)


if __name__ == "__main__":
    main()
