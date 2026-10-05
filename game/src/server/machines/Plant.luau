-- Things that grow: a sapling becomes a tree of blocks, a crop ripens through stages.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local IslandGen = require(Shared.IslandGen)
local IslandService = require(script.Parent.Parent.IslandService)
local Kit = require(script.Parent.Parent.MachineKit)
local Tuning = require(script.Parent.Parent.Tuning)

local Plant = {}

Plant.WET_RATE = 2 -- how many times faster a watered plant grows

local function stageOf(machine): number
	local stages = machine.def.stages
	if not stages then
		return 1
	end
	return math.clamp(math.floor(machine.age / Config.CROP_SECONDS * (#stages - 1)) + 1, 1, #stages)
end

local function show(machine, stage: number)
	if machine.visual then
		machine.visual:Destroy()
	end
	local stages = machine.def.stages
	machine.stage = stage
	machine.visual = Kit.visual(machine.model, machine.base, if stages then stages[stage] else machine.id)
end

function Plant.build(machine)
	machine.age = 0
	machine.wetUntil = 0
	show(machine, 1)
	Kit.body(machine)
end

function Plant.load(machine, saved)
	if type(saved) == "table" and type(saved.age) == "number" and saved.age == saved.age then
		machine.age = math.clamp(saved.age, 0, 100000)
		local stage = stageOf(machine)
		if stage ~= machine.stage then
			show(machine, stage)
		end
	end
end

function Plant.save(machine)
	return { age = math.floor(machine.age) }
end

-- Keeps the plant watered for a while. A sprinkler calls this again and again.
function Plant.water(machine, seconds: number)
	machine.wetUntil = os.clock() + seconds
end

-- Returning true asks the machine service to remove this plant and then call `finish`.
function Plant.tick(machine, dt: number): boolean
	local rate = if os.clock() < machine.wetUntil then Plant.WET_RATE else 1
	machine.age += dt * Tuning.speed * rate
	if machine.def.behavior == "sapling" then
		return machine.age >= Config.SAPLING_SECONDS
	end
	local stage = stageOf(machine)
	if stage ~= machine.stage then
		show(machine, stage)
	end
	return false
end

-- A grown sapling leaves a tree where it stood. Cells that are already taken are skipped.
function Plant.finish(machine)
	local blocks = {}
	IslandGen.tree(blocks, machine.x, machine.y, machine.z, 3)
	for _, b in blocks do
		IslandService.setBlock(machine.island, b.x, b.y, b.z, b.id)
	end
end

function Plant.isRipe(machine): boolean
	local stages = machine.def.stages
	return stages ~= nil and machine.stage == #stages
end

-- Gathers a ripe crop without digging it up: the plant starts again from a seedling, and what it
-- bore is returned. The seed it would have dropped is the one left growing.
function Plant.harvest(machine): { [string]: number }?
	if not Plant.isRipe(machine) then
		return nil
	end
	machine.age = 0
	show(machine, 1)
	return { wheat = 2 }
end

function Plant.drops(machine): { [string]: number }
	if machine.def.behavior == "sapling" then
		return { sapling = 1 }
	end
	if Plant.isRipe(machine) then
		return { wheat = 2, seed = 1 }
	end
	return { seed = 1 }
end

return Plant
