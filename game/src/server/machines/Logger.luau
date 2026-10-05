-- The logger: cuts the trees near it, one log at a time from the top down, and puts the logs out
-- of its mouth. When a tree is finished it clears the leaves and sets a sapling where the tree
-- stood, so a stand of trees keeps itself going.
-- It cannot tell a tree from a pillar of log blocks someone built: any log in reach is cut.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local FarmLogic = require(Shared.FarmLogic)
local Grid = require(Shared.Grid)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local IslandService = require(script.Parent.Parent.IslandService)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineService = require(script.Parent.Parent.MachineService)
local Outlet = require(script.Parent.Parent.Outlet)
local Tuning = require(script.Parent.Parent.Tuning)

local Logger = {}

local RADIUS = 3 -- cells each way
local BELOW, ABOVE = 1, 8 -- how far under and over its own level it looks for logs
local EVERY = 3 -- seconds per log
local HOLDS = 8 -- cut logs waiting to come out before it stops cutting
local REPLANT = true
local SAPLING = "plant_sapling"

function Logger.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	Kit.body(machine)
	machine.out = Kit.outputs(Kit.ports(machine))[1]
	machine.waiting = 0 -- logs cut but not yet put out
	machine.wait = EVERY
end

function Logger.load(machine, saved)
	if type(saved) == "table" and type(saved.waiting) == "number" and saved.waiting == saved.waiting then
		machine.waiting = math.clamp(math.floor(saved.waiting), 0, HOLDS)
	end
end

function Logger.save(machine)
	return { waiting = machine.waiting }
end

local function cut(machine)
	local island = machine.island
	local function isLog(x: number, y: number, z: number): boolean
		return DeviceKit.blockAt(island, x, y, z) == "log"
	end
	local function isLeaf(x: number, y: number, z: number): boolean
		return DeviceKit.blockAt(island, x, y, z) == "leaves"
	end
	local log = FarmLogic.nextLog(isLog, machine.x, machine.y, machine.z, RADIUS, BELOW, ABOVE)
	if not log then
		return
	end
	IslandService.clearCell(island, Grid.key(log.x, log.y, log.z))
	machine.waiting += 1
	if FarmLogic.trunkStands(isLog, log.x, log.z, machine.y - BELOW, machine.y + ABOVE) then
		return
	end
	-- That was the last log of the tree, and since trees come down from the top, the lowest.
	for _, leaf in FarmLogic.looseLeaves(isLeaf, isLog, log.x, log.y, log.z) do
		IslandService.clearCell(island, Grid.key(leaf.x, leaf.y, leaf.z))
	end
	local ground = DeviceKit.blockAt(island, log.x, log.y - 1, log.z)
	local needs = Defs.Machines[SAPLING].needsBelow or {}
	if
		REPLANT
		and ground
		and table.find(needs, ground)
		and Grid.inBounds(log.x, log.y, log.z, Config.MAX_COORD)
	then
		MachineService.create(island, SAPLING, log.x, log.y, log.z, 0, nil)
	end
end

function Logger.tick(machine, dt: number)
	if machine.waiting > 0 and machine.out and Outlet.emit(machine, machine.out, "log") then
		machine.waiting -= 1
	end
	machine.wait -= dt * Tuning.speed
	if machine.wait <= 0 and machine.waiting < HOLDS then
		machine.wait = EVERY
		cut(machine)
	end
end

function Logger.drops(machine): { [string]: number }
	return if machine.waiting > 0 then { log = machine.waiting } else {}
end

return Logger
