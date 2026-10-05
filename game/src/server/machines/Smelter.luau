-- Takes ore and coal in at the back, burns the coal, and puts ingots out at the front.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local SmelterLogic = require(Shared.SmelterLogic)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)

local Smelter = {}
local C = Kit.COLORS

local RULES: SmelterLogic.Rules = {
	smeltTime = Config.SMELT_TIME,
	fuelPerCoal = Config.FUEL_PER_COAL,
	maxFuel = Config.SMELTER_MAX_FUEL,
	maxOre = Config.SMELTER_MAX_ORE,
	maxOut = Config.SMELTER_MAX_OUT,
}
local INTAKE_SIZE = Vector3.new(0.5, 0.9, 2.2)
local MOUTH_SIZE = Vector3.new(0.9, 0.9, 2.2)

function Smelter.build(machine)
	local model, base = machine.model, machine.base
	Kit.lip(model, base, -1.05, 0.9, Config.BELT_SPEED)
	Kit.lip(model, base, 1.05, 0.9, Config.BELT_SPEED)
	Kit.part(model, base, Vector3.new(1.2, 2.6, 2.8), Vector3.new(0, -0.2, 0), C.body)
	Kit.part(model, base, Vector3.new(1.3, 0.2, 2.9), Vector3.new(0, 1.2, 0), C.dark)
	Kit.part(model, base, Vector3.new(0.5, 1.2, 0.5), Vector3.new(0, 1.9, -0.8), C.body)
	Kit.detail(model, base, Vector3.new(0.62, 0.15, 0.62), Vector3.new(0, 2.55, -0.8), C.dark)
	Kit.mouth(model, base, -0.6, true)
	Kit.mouth(model, base, 0.6, false)

	machine.windows = {}
	for _, z in { -1.41, 1.41 } do
		local window = Kit.detail(model, base, Vector3.new(0.8, 0.6, 0.06), Vector3.new(0, -0.2, z), C.hole)
		table.insert(machine.windows, window)
	end

	machine.intakeBox = base * CFrame.new(-0.85, -0.25, 0)
	machine.mouthBox = base * CFrame.new(1.05, -0.25, 0)
	machine.spawnAt = base * CFrame.new(1.0, -0.2, 0)
	machine.state = SmelterLogic.new()
	machine.lit = false
end

function Smelter.load(machine, saved)
	machine.state = SmelterLogic.sanitize(saved, RULES)
end

function Smelter.save(machine)
	local s = machine.state
	return { fuel = s.fuel, ore = s.ore, out = s.out }
end

function Smelter.tick(machine, dt: number)
	local state = machine.state
	for _, part in ItemService.inBox(machine.intakeBox, INTAKE_SIZE) do
		local id, count = ItemService.info(part)
		if id then
			local wanted = math.min(count, SmelterLogic.room(state, id, RULES))
			if wanted > 0 then
				SmelterLogic.insert(state, id, ItemService.take(part, wanted), RULES)
			end
		end
	end

	SmelterLogic.step(state, dt, RULES)

	if state.out > 0 and #ItemService.inBox(machine.mouthBox, MOUTH_SIZE) == 0 then
		SmelterLogic.takeOutput(state, 1)
		ItemService.spawn("iron_ingot", 1, machine.spawnAt.Position)
	end

	local lit = SmelterLogic.isWorking(state, RULES)
	if lit ~= machine.lit then
		machine.lit = lit
		for _, window in machine.windows do
			window.Color = if lit then C.glow else C.hole
			window.Material = if lit then Enum.Material.Neon else Enum.Material.SmoothPlastic
		end
	end
end

-- What falls out when the smelter is broken.
function Smelter.drops(machine): { [string]: number }
	local s = machine.state
	return {
		iron_ore = s.ore,
		iron_ingot = s.out,
		coal = math.floor(s.fuel / RULES.fuelPerCoal),
	}
end

return Smelter
