on run argv
	set dir1 to posix file (item 1 of argv)
	set dir2 to posix file (item 2 of argv)
	tell application "finder"
		with timeout of 999999999 seconds
			try
				duplicate dir1 to dir2
            on error errmsg number errnum
                display dialog errmsg & errnum
			end try
		end timeout
	end tell
end run