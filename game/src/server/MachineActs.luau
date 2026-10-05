-- One door for everything a player does to a placed machine beyond placing and breaking it:
-- choosing what an assembler makes, stocking a vending machine, buying from one, flipping a switch.
-- The request names the island's owner and a cell, so visitors can use machines on islands that are
-- not theirs. This module checks the request is sane and the player is close; whether that player
-- may do that thing is for the machine to decide in its own `act` function:
--     function Module.act(machine, player: Player, action: string, arg: any)
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Grid = require(Shared.Grid)
local Net = require(Shared.Net)
local IslandService = require(script.Parent.IslandService)
local MachineService = require(script.Parent.MachineService)
local RateLimit = require(script.Parent.RateLimit)

local MachineActs = {}

local function onAct(player: Player, ownerId: any, x: any, y: any, z: any, action: any, arg: any)
	if not RateLimit.allow(player) then
		return
	end
	if type(ownerId) ~= "number" or type(action) ~= "string" or #action > 32 then
		return
	end
	if
		not (Grid.isInt(x) and Grid.isInt(y) and Grid.isInt(z))
		or not Grid.inBounds(x, y, z, Config.MAX_COORD)
	then
		return
	end
	local island = IslandService.byUserId(ownerId)
	local machine = island and MachineService.at(island, x, y, z)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not machine or not machine.mod.act or not root or not root:IsA("BasePart") then
		return
	end
	if (machine.center - root.Position).Magnitude > Config.REACH then
		return
	end
	local ok, err = pcall(machine.mod.act, machine, player, action, arg)
	if not ok then
		warn("machine act " .. action .. " on " .. machine.id .. " failed: " .. tostring(err))
	end
end

-- Tells a player's client to show a machine's screen. `info` is whatever that screen needs; the
-- client is also given what it must send back to act on this machine.
function MachineActs.show(player: Player, machine, kind: string, info: { [string]: any }?)
	Net.get("MachineInfo"):FireClient(player, {
		kind = kind,
		id = machine.id,
		owner = machine.island.owner.UserId,
		x = machine.x,
		y = machine.y,
		z = machine.z,
		info = info or {},
	})
end

function MachineActs.start()
	Net.get("MachineAct").OnServerEvent:Connect(onAct)
end

return MachineActs
