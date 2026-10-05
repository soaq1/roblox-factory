-- Belts carry anything that touches them. There is no code moving the items: the surface has a
-- velocity and the physics engine does the rest.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)
local Kit = require(script.Parent.Parent.MachineKit)

local Belt = {}
local C = Kit.COLORS

local function chevron(model: Instance, base: CFrame, x: number, z: number, heading: number)
	local at = base * CFrame.new(x, -0.69, z) * CFrame.Angles(0, -heading, 0)
	for _, side in { -1, 1 } do
		Kit.detail(
			model,
			at,
			Vector3.new(0.7, 0.03, 0.14),
			Vector3.new(0, 0, side * 0.22),
			C.mark,
			CFrame.Angles(0, side * math.rad(42), 0)
		)
	end
end

function Belt.build(machine)
	local model, base = machine.model, machine.base
	local speed = Config.BELT_SPEED
	local shape = machine.def.shape
	Kit.part(model, base, Vector3.new(3, 0.6, 3), Vector3.new(0, -1.2, 0), C.dark)

	if shape == "straight" then
		Kit.conveyor(
			model,
			base,
			Vector3.new(3, 0.2, 2.35),
			Vector3.new(0, -0.8, 0),
			Vector3.new(speed, 0, 0)
		)
		for _, z in { -1.3, 1.3 } do
			Kit.part(model, base, Vector3.new(3, 0.6, 0.25), Vector3.new(0, -0.6, z), C.light)
		end
		chevron(model, base, 0, 0, 0)
	elseif shape == "merge" then
		-- No side rails: items can roll on from either side and are carried forward. Two angled
		-- guides at the front funnel them back to the width of the next belt.
		Kit.conveyor(model, base, Vector3.new(3, 0.2, 3), Vector3.new(0, -0.8, 0), Vector3.new(speed, 0, 0))
		for _, z in { -1, 1 } do
			local guide =
				Kit.part(model, base, Vector3.new(1.25, 0.6, 0.2), Vector3.new(0.9, -0.6, z * 1.34), C.light)
			guide.CFrame *= CFrame.Angles(0, z * math.rad(15.2), 0)
			chevron(model, base, -0.2, z, 0)
		end
		chevron(model, base, 0, 0, 0)
	else
		-- Enters travelling forward, leaves to the right (+Z) or left (-Z). The surface pushes
		-- diagonally and the two outer walls turn that into a clean corner.
		local side = if shape == "right" then 1 else -1
		local push = speed * 0.7071
		Kit.conveyor(
			model,
			base,
			Vector3.new(3, 0.2, 3),
			Vector3.new(0, -0.8, 0),
			Vector3.new(push, 0, side * push)
		)
		Kit.part(model, base, Vector3.new(0.25, 0.6, 3), Vector3.new(1.3, -0.6, 0), C.light)
		Kit.part(model, base, Vector3.new(2.675, 0.6, 0.25), Vector3.new(-0.1625, -0.6, -side * 1.3), C.light)
		Kit.part(model, base, Vector3.new(0.3, 0.6, 0.3), Vector3.new(-1.35, -0.6, side * 1.35), C.light)
		chevron(model, base, -0.6, 0, 0)
		chevron(model, base, 0, side * 0.6, side * math.pi / 2)
	end
end

return Belt
