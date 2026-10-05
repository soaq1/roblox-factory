-- This player's settings and saved hotbar, as last heard from the server, and the way to change
-- them. Other client code reads a setting with Settings.get("holdToRepeat").
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared:WaitForChild("Net"))
local Prefs = require(Shared:WaitForChild("Prefs"))

local Settings = {}

Settings.DEFAULTS = Prefs.DEFAULTS

local values: { [string]: boolean } = {}
local bar: { string } = {}
local loaded = false
local listeners: { () -> () } = {}

local function tell()
	for _, run in listeners do
		task.spawn(run)
	end
end

function Settings.get(name: string): boolean
	return Prefs.value(values, name)
end

function Settings.set(name: string, value: boolean)
	if Prefs.DEFAULTS[name] == nil or Settings.get(name) == value then
		return
	end
	values[name] = value
	Net.get("Prefs"):FireServer("setting", name, value)
	tell()
end

-- Runs `run` whenever a setting changes or the saved ones arrive.
function Settings.onChange(run: () -> ())
	table.insert(listeners, run)
end

-- Has the server's copy arrived yet?
function Settings.isLoaded(): boolean
	return loaded
end

-- The hotbar as it was last saved: ten entries, or an empty list if it was never saved.
function Settings.savedBar(): { string }
	return bar
end

function Settings.saveBar(slots: { string })
	bar = table.clone(slots)
	Net.get("Prefs"):FireServer("bar", bar)
end

function Settings.init()
	Net.get("Prefs").OnClientEvent:Connect(function(saved)
		if type(saved) ~= "table" then
			return
		end
		values = if type(saved.settings) == "table" then saved.settings else {}
		bar = if type(saved.bar) == "table" then saved.bar else {}
		loaded = true
		tell()
	end)
	-- The island may not exist yet when this runs, so keep asking until an answer comes.
	task.spawn(function()
		while not loaded do
			Net.get("Prefs"):FireServer("load")
			task.wait(1)
		end
	end)
end

return Settings
