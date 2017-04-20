# directory that should be watched for changes
# mandatory
wpath = "/home/user/www" # MUST BE ABSOLUTE PATH

# exclude list for rsync
rexcludes = [
	"*/6/*",
	"*.bin",
]

# directory where changes will be rsynced
# mandatory
rpath = "/var/lib/www" # MUST BE ABSOLUTE PATH

# remote locations in rsync syntax, use "" for local, or "user@host:" for remote
# mandatory
rnodes = [
	"user1@a.mirror.com:",
	"user2@b.mirror.com:",
	"user3@c.mirror.com:",
]

# rsync binary path
# for test purpose, use "/bin/echo rsync"
# defaults to "/usr/bin/rsync"
#rsync = "/usr/bin/rsync" # MUST BE ABSOLUTE PATH

# extra parameters to rsync
#extra = "--rsh=ssh -a"

# limit remote sync speed (in KB/s, 0 = no limit)
# defaults to 0
#rspeed = 0

# rsync log file for updates
logfile = "log/inosync.log"
