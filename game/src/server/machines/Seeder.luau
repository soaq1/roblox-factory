-- The seeder: sows the seeds delivered to it on empty farmland near it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local FarmLogic = require(Shared.FarmLogic)
local Inventory = require(Shared.Inventory)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineService = require(script.Parent.Parent.MachineService)
local Tuning = require(script.Parent.Parent.Tuning)

local Seeder = {}

local RADIUS = 2 -- cells each way, so a 5 by 5 patch
local EVERY = 1 -- seconds between one sowing and the next
local HOLDS = 16 -- seeds of one kind it keeps ready

-- Which crop grows from which seed, and the ground it needs.
local crops: { [string]: string } = {}
for id, def in Defs.Machines do
	if def.behavior == "crop" and def.cost and not def.hidden then
		crops[def.cost] = id
	end
end

local function wanted(machine, id: string): boolean
	return crops[id] ~= nil and (machine.state[id] or 0) < HOLDS
end

local function describe(machine): string
	local parts = {}
	for id, n in machine.state do
		table.insert(parts, Defs.name(id) .. " " .. n)
	end
	table.sort(parts)
	return if #parts > 0 then table.concat(parts, " · ") else "씨앗 없음"
end

function Seeder.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.ins = Kit.inputs(Kit.ports(machine))
	machine.state = {}
	machine.wait = 0
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
end

function Seeder.load(machine, saved)
	machine.state = {}
	for id, n in Inventory.sanitize(saved, Defs.isItem) do
		if crops[id] then
			machine.state[id] = math.min(n, HOLDS)
		end
	end
end

function Seeder.save(machine)
	return table.clone(machine.state)
end

-- Called when a neighbouring machine hands an item straight over.
function Seeder.accept(machine, id: string, _n: number): number
	if not wanted(machine, id) then
		return 0
	end
	Inventory.add(machine.state, id, 1)
	return 1
end

function Seeder.tick(machine, dt: number)
	local taken = DeviceKit.pull(machine, function(id)
		return wanted(machine, id)
	end)
	if taken then
		Inventory.add(machine.state, taken, 1)
	end

	machine.wait -= dt * Tuning.speed
	local seed = next(machine.state)
	if machine.wait <= 0 and seed then
		machine.wait = EVERY
		local island = machine.island
		local crop = crops[seed]
		local ground = Defs.Machines[crop].needsBelow or {}
		local spot = FarmLogic.nearest(function(x, y, z)
			local below = DeviceKit.blockAt(island, x, y - 1, z)
			return below ~= nil and table.find(ground, below) ~= nil and DeviceKit.isFree(island, x, y, z)
		end, machine.x, machine.y, machine.z, RADIUS)
		if spot and MachineService.create(island, crop, spot.x, spot.y, spot.z, 0, nil) then
			Inventory.remove(machine.state, seed, 1)
		end
	end

	local text = describe(machine)
	if text ~= machine.shown then
		machine.shown = text
		machine.label.Text = text
	end
end

function Seeder.drops(machine): { [string]: number }
	return table.clone(machine.state)
end

return Seeder
