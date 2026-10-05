-- The harvester: gathers ripe crops near it and puts what they bore out of its mouth. The crops
-- are left in the ground to grow again.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local FarmLogic = require(Shared.FarmLogic)
local Inventory = require(Shared.Inventory)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local Outlet = require(script.Parent.Parent.Outlet)
local Tuning = require(script.Parent.Parent.Tuning)
local Plant = require(script.Parent.Plant)

local Harvester = {}

local RADIUS = 2 -- cells each way, so a 5 by 5 patch
local EVERY = 1 -- seconds between one crop and the next
local HOLDS = 16 -- gathered items waiting to come out before it stops gathering

local function held(machine): number
	local total = 0
	for _, n in machine.state do
		total += n
	end
	return total
end

function Harvester.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	Kit.body(machine)
	machine.out = Kit.outputs(Kit.ports(machine))[1]
	machine.state = {}
	machine.wait = 0
end

function Harvester.load(machine, saved)
	machine.state = Inventory.sanitize(saved, Defs.isItem)
end

function Harvester.save(machine)
	return table.clone(machine.state)
end

function Harvester.tick(machine, dt: number)
	local id = next(machine.state)
	if id and machine.out and Outlet.emit(machine, machine.out, id) then
		Inventory.remove(machine.state, id, 1)
	end

	machine.wait -= dt * Tuning.speed
	if machine.wait > 0 or held(machine) >= HOLDS then
		return
	end
	machine.wait = EVERY
	local island = machine.island
	local spot = FarmLogic.nearest(function(x, y, z)
		local other = DeviceKit.machineAt(island, x, y, z)
		return other ~= nil and other.mod == Plant and Plant.isRipe(other)
	end, machine.x, machine.y, machine.z, RADIUS)
	local crop = spot and DeviceKit.machineAt(island, spot.x, spot.y, spot.z)
	local yield = crop and Plant.harvest(crop)
	for item, n in yield or {} do
		Inventory.add(machine.state, item, n)
	end
end

function Harvester.drops(machine): { [string]: number }
	return table.clone(machine.state)
end

return Harvester
