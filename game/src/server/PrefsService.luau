-- Keeps each player's hotbar and settings: sends them when the island is ready and takes changes.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Net = require(Shared.Net)
local Prefs = require(Shared.Prefs)
local IslandService = require(script.Parent.IslandService)
local RateLimit = require(script.Parent.RateLimit)

local PrefsService = {}

-- The value of one of a player's settings, for other systems to ask.
function PrefsService.setting(player: Player, name: string): boolean
	local island = IslandService.get(player)
	return Prefs.value(if island then island.prefs.settings else {}, name)
end

local function onPrefs(player: Player, what: any, a: any, b: any)
	local island = IslandService.get(player)
	if not island or not RateLimit.allow(player) then
		return
	end
	if what == "load" then
		-- The client asks once it is ready to listen, so nothing is sent into the void.
		Net.get("Prefs"):FireClient(player, island.prefs)
	elseif what == "bar" then
		island.prefs.bar = Prefs.cleanBar(a, Defs.isEntry)
	elseif
		what == "setting"
		and type(a) == "string"
		and Prefs.DEFAULTS[a] ~= nil
		and type(b) == "boolean"
	then
		island.prefs.settings[a] = b
	end
end

function PrefsService.start()
	Net.get("Prefs").OnServerEvent:Connect(onPrefs)
end

return PrefsService
