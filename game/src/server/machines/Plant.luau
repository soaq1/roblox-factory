-- Things that grow: a sapling becomes a tree, a crop ripens through stages.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local TreeGen = require(Shared.TreeGen)
local Inventory = require(Shared.Inventory)
local MachineService = require(script.Parent.Parent.MachineService)
local Kit = require(script.Parent.Parent.MachineKit)
local Profile = require(script.Parent.Parent.Profile)
local Tuning = require(script.Parent.Parent.Tuning)

local Plant = {}

Plant.WET_RATE = 2 -- how many times faster a watered plant grows
Plant.LOOK_SECONDS = 5 -- how often a grown sapling looks for room to become a tree

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
	-- The "gather" prompt is only there while there is something to gather.
	if machine.prompt then
		machine.prompt.Enabled = stages ~= nil and stage == #stages
	end
end

function Plant.build(machine)
	machine.age = 0
	machine.wetUntil = 0
	show(machine, 1)
	local body = Kit.body(machine)
	machine.body = body
	if machine.def.behavior == "sapling" then
		-- What tree this will be is settled when it is planted, so it can be asked whether that
		-- tree has room, and so it does not change if the island is saved in between.
		machine.grow = { seed = math.random(1, 2 ^ 30), giant = TreeGen.isGiant(math.random()) }
	end
	if machine.def.stages then
		-- F on a ripe crop gathers it by hand, the way the harvester does: what it bore goes into
		-- the bag and the plant starts over where it stands.
		machine.prompt = Kit.prompt(machine, body, "거두기", function(player)
			if player ~= machine.island.owner then
				return
			end
			local yield = Plant.harvest(machine)
			if not yield then
				return
			end
			for id, count in yield do
				Inventory.add(machine.island.bag, id, count)
			end
			Profile.push(machine.island)
		end)
		machine.prompt.Enabled = false
	end
end

function Plant.load(machine, saved)
	if type(saved) == "table" and type(saved.age) == "number" and saved.age == saved.age then
		machine.age = math.clamp(saved.age, 0, 100000)
		local stage = stageOf(machine)
		if stage ~= machine.stage then
			show(machine, stage)
		end
	end
	if
		machine.grow
		and type(saved) == "table"
		and type(saved.seed) == "number"
		and saved.seed == saved.seed
	then
		machine.grow = { seed = math.clamp(math.floor(saved.seed), 1, 2 ^ 30), giant = saved.giant == true }
	end
end

function Plant.save(machine)
	local grow = machine.grow
	return {
		age = math.floor(machine.age),
		seed = if grow then grow.seed else nil,
		giant = if grow then grow.giant else nil,
	}
end

-- Keeps the plant watered for a while. A sprinkler calls this again and again.
function Plant.water(machine, seconds: number)
	machine.wetUntil = os.clock() + seconds
end

-- Returning true asks the machine service to remove this plant and then call `finish`.
-- Is there room for the tree this sapling will become? A sapling due to be a giant settles for
-- an ordinary tree when the giant does not fit.
local function hasRoom(machine): boolean
	local grow = machine.grow
	local function fits(giant: boolean): boolean
		local want = { seed = grow.seed, giant = giant }
		local keys = MachineService.freeCells(
			machine.island,
			"tree",
			machine.x,
			machine.y,
			machine.z,
			0,
			want,
			machine
		)
		return keys ~= nil
	end
	if grow.giant and fits(true) then
		return true
	end
	if fits(false) then
		grow.giant = false
		return true
	end
	return false
end

function Plant.tick(machine, dt: number): boolean
	local rate = if os.clock() < machine.wetUntil then Plant.WET_RATE else 1
	machine.age += dt * Tuning.speed * rate
	if machine.def.behavior == "sapling" then
		if machine.age < Config.SAPLING_SECONDS then
			return false
		end
		-- Grown: it becomes a tree as soon as the tree has room. Looking is not free, so it looks
		-- now and then rather than every beat.
		machine.lookIn = (machine.lookIn or 0) - dt
		if machine.lookIn > 0 then
			return false
		end
		machine.lookIn = Plant.LOOK_SECONDS
		if hasRoom(machine) then
			return true
		end
		if not machine.blockedLabel then
			machine.blockedLabel = Kit.label(machine.body, machine.def.height)
			machine.blockedLabel.Text = "자랄 자리가 막혀 있음"
		end
		return false
	end
	local stage = stageOf(machine)
	if stage ~= machine.stage then
		show(machine, stage)
	end
	return false
end

-- A grown sapling leaves a tree where it stood. Cells that are already taken are skipped.
function Plant.finish(machine)
	MachineService.create(machine.island, "tree", machine.x, machine.y, machine.z, 0, machine.grow)
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
