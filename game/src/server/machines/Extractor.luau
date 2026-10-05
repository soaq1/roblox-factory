-- Puts out one raw item at a steady pace. Which item depends on the vein core it was made with.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)

local Extractor = {}
local C = Kit.COLORS

-- Debug control: how many times faster than normal extractors run.
Extractor.speed = 1

function Extractor.build(machine)
	local model, base = machine.model, machine.base
	local core = machine.def.core
	local coreColor = Color3.fromRGB(core[1], core[2], core[3])

	Kit.part(model, base, Vector3.new(1.9, 2.5, 2.7), Vector3.new(-0.55, -0.25, 0), C.body)
	Kit.part(model, base, Vector3.new(2.0, 0.2, 2.8), Vector3.new(-0.55, 1.1, 0), C.dark)
	for _, x in { -1.15, 0.05 } do
		for _, z in { -0.6, 0.6 } do
			Kit.detail(model, base, Vector3.new(0.2, 0.8, 0.2), Vector3.new(x, 1.6, z), C.light)
		end
	end
	local crystal = Kit.detail(
		model,
		base,
		Vector3.new(0.8, 0.8, 0.8),
		Vector3.new(-0.55, 1.95, 0),
		coreColor,
		CFrame.Angles(math.rad(45), 0, math.rad(35))
	)
	crystal.Material = Enum.Material.Neon
	Kit.mouth(model, base, 0.4, false)
	Kit.lip(model, base, 0.95, 1.1, Config.BELT_SPEED)

	machine.spawnAt = base * CFrame.new(0.9, -0.2, 0)
	machine.mouthBox = base * CFrame.new(0.95, -0.25, 0)
	machine.timer = 0
end

local MOUTH_SIZE = Vector3.new(1.0, 0.9, 2.2)

function Extractor.tick(machine, dt: number)
	machine.timer = math.min(machine.timer + dt * Extractor.speed, Config.EXTRACT_INTERVAL)
	if machine.timer < Config.EXTRACT_INTERVAL then
		return
	end
	-- Wait while the last item is still sitting in the mouth, so a blocked line backs up instead of piling.
	if #ItemService.inBox(machine.mouthBox, MOUTH_SIZE) > 0 then
		return
	end
	machine.timer = 0
	ItemService.spawn(machine.def.item, 1, machine.spawnAt.Position)
end

return Extractor
