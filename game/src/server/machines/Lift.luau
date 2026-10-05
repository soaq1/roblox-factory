-- The lift: takes an item in at the bottom and puts it out at the front two levels up.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local Outlet = require(script.Parent.Parent.Outlet)

local Lift = {}

local RISE_CELLS = 2
local RISE_SECONDS = 1.5 -- how long an item spends going up
local CAPACITY = 4 -- items on their way up at once

function Lift.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
	machine.ins = Kit.inputs(Kit.ports(machine))
	local up = RISE_CELLS * Config.CELL
	machine.out = DeviceKit.mouth(machine, "out", Vector3.new(Config.CELL / 2, up, 0), Vector3.xAxis)
	machine.queue = {} -- oldest first: { id, left } with the seconds it still has to climb
end

function Lift.load(machine, saved)
	if type(saved) ~= "table" or type(saved.queue) ~= "table" then
		return
	end
	for _, id in saved.queue do
		if Defs.isItem(id) and #machine.queue < CAPACITY then
			table.insert(machine.queue, { id = id, left = 0 })
		end
	end
end

function Lift.save(machine)
	local ids = {}
	for _, entry in machine.queue do
		table.insert(ids, entry.id)
	end
	return { queue = ids }
end

-- Called when a neighbouring machine hands an item straight over.
function Lift.accept(machine, id: string, _n: number): number
	if #machine.queue >= CAPACITY then
		return 0
	end
	table.insert(machine.queue, { id = id, left = RISE_SECONDS })
	return 1
end

function Lift.tick(machine, dt: number)
	local queue = machine.queue
	machine.busy = #queue > 0 -- an empty lift draws no power
	if DeviceKit.unpowered(machine) then
		DeviceKit.say(machine, DeviceKit.NO_POWER)
		return
	end
	DeviceKit.say(machine, "")
	if #queue < CAPACITY then
		local id = DeviceKit.pull(machine)
		if id then
			table.insert(queue, { id = id, left = RISE_SECONDS })
		end
	end
	for _, entry in queue do
		entry.left -= dt
	end
	local first = queue[1]
	if first and first.left <= 0 and Outlet.emit(machine, machine.out, first.id) then
		table.remove(queue, 1)
	end
end

function Lift.drops(machine): { [string]: number }
	local all = {}
	for _, entry in machine.queue do
		all[entry.id] = (all[entry.id] or 0) + 1
	end
	return all
end

return Lift
