-- The logger: fells the trees near it, one at a time, and puts the logs out of its mouth. It
-- sets a sapling back where each tree stood, so a stand of trees keeps itself going, and puts any
-- sapling left over out with the logs.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineService = require(script.Parent.Parent.MachineService)
local Outlet = require(script.Parent.Parent.Outlet)
local Tuning = require(script.Parent.Parent.Tuning)

local Logger = {}

local RADIUS = 3 -- cells each way, measured to where the trunk stands
local EVERY = 12 -- seconds between trees (a placeholder)
local HOLDS = 8 -- things waiting to come out before it stops felling
local REPLANT = true
local SAPLING = "plant_sapling"

local function count(stock: { [string]: number }): number
	local total = 0
	for _, n in stock do
		total += n
	end
	return total
end

function Logger.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	Kit.body(machine)
	machine.out = Kit.outputs(Kit.ports(machine))[1]
	machine.stock = {} -- felled but not yet put out: logs, and saplings it had no use for
	machine.wait = EVERY
end

function Logger.load(machine, saved)
	if type(saved) ~= "table" then
		return
	end
	-- an older save held only a number of logs
	local stock = if type(saved.stock) == "table" then saved.stock else { log = saved.waiting }
	for _, id in { "log", "sapling" } do
		local n = stock[id]
		if type(n) == "number" and n == n and n >= 1 then
			machine.stock[id] = math.min(math.floor(n), 999)
		end
	end
end

function Logger.save(machine)
	return { stock = table.clone(machine.stock) }
end

-- The nearest tree whose trunk stands within reach, on the logger's own level or near it.
local function nearestTree(machine)
	local best, bestDistance = nil, math.huge
	for _, other in MachineService.onIsland(machine.island) do
		if other.def.behavior == "tree" then
			local dx, dz = math.abs(other.x - machine.x), math.abs(other.z - machine.z)
			if dx <= RADIUS and dz <= RADIUS and math.abs(other.y - machine.y) <= 1 then
				local distance = dx + dz
				if distance < bestDistance then
					best, bestDistance = other, distance
				end
			end
		end
	end
	return best
end

local function fell(machine)
	local tree = nearestTree(machine)
	if not tree then
		return
	end
	local island, x, y, z = machine.island, tree.x, tree.y, tree.z
	local yield = tree.mod.drops(tree) -- this is also what makes the tree tip over
	MachineService.remove(tree, false)
	-- One sapling goes back where the tree stood, if the ground still suits it.
	local ground = DeviceKit.blockAt(island, x, y - 1, z)
	local needs = Defs.Machines[SAPLING].needsBelow or {}
	if REPLANT and (yield.sapling or 0) >= 1 and ground and table.find(needs, ground) then
		if MachineService.create(island, SAPLING, x, y, z, 0, nil) then
			yield.sapling -= 1
		end
	end
	for id, n in yield do
		if n > 0 then
			machine.stock[id] = (machine.stock[id] or 0) + n
		end
	end
end

function Logger.tick(machine, dt: number)
	local id = next(machine.stock)
	if id and machine.out and Outlet.emit(machine, machine.out, id) then
		local left = machine.stock[id] - 1
		machine.stock[id] = if left > 0 then left else nil
	end
	machine.wait -= dt * Tuning.speed
	if machine.wait <= 0 and count(machine.stock) < HOLDS then
		machine.wait = EVERY
		fell(machine)
	end
end

function Logger.drops(machine): { [string]: number }
	return table.clone(machine.stock)
end

return Logger
