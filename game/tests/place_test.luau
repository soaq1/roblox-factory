-- Runs outside Roblox:  lune run tests/place_test.luau
-- Checks the settings in the Rojo project files that the game cannot check for itself. A place
-- built by Rojo only gets the properties named here; everything else takes the class default,
-- which is not always what a place made in Studio starts with.
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local T = require("./harness")
local test, eq = T.test, T.eq

local PROJECTS = { "default.project.json", "build.project.json" }

local function tree(file: string): any
	return serde.decode("json", fs.readFile(file)).tree
end

for _, file in PROJECTS do
	-- Without this the place runs the old chat system, which Roblox has removed: the chat bar does
	-- nothing, TextChatCommands never fire, and Player.Chatted never runs. No error is reported.
	test(file .. " turns on the current chat system", function()
		local service = tree(file).TextChatService
		if not service then
			error("no TextChatService entry", 2)
		end
		eq(service["$properties"].ChatVersion, "TextChatService", "ChatVersion")
	end)
	-- The two files have to describe the same game; the build one only adds the imported meshes.
	test(file .. " keeps the same services as the other project file", function()
		local other = tree(if file == PROJECTS[1] then PROJECTS[2] else PROJECTS[1])
		for name in tree(file) do
			if not other[name] then
				error(name .. " is missing from the other project file", 2)
			end
		end
	end)
end

T.done()
