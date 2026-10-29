use framework "Foundation"
use scripting additions

on run argv
  if (count argv) is not 2 then error "Pass the candidate path and exact running editor app path"
  set requestedPath to item 1 of argv
  set editorPath to item 2 of argv
  set expectedURL to current application's NSURL's fileURLWithPath:requestedPath
  set expectedPath to (expectedURL's URLByResolvingSymlinksInPath()'s |path|()) as text
  using terms from application "Camtasia"
    with timeout of 25 seconds
      repeat 2 times
        tell application editorPath
          if (count documents) is not 0 then error "Save and close other Camtasia documents before running the native adapter"
          open POSIX file requestedPath
          if (count documents) is not 1 then error "Expected only the requested candidate; no document was saved"
          set documentURL to path of document 1
        end tell
        set actualURL to current application's NSURL's URLWithString:documentURL
        set actualPath to (actualURL's URLByResolvingSymlinksInPath()'s |path|()) as text
        if actualPath is not expectedPath then error "Camtasia did not open the requested candidate; no document was saved"
        tell application editorPath
          save document 1
          close document 1 saving yes
        end tell
      end repeat
    end timeout
  end using terms from
  return requestedPath
end run
