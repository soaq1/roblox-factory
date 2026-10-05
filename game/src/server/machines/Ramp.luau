-- The ramp belt: two cells long, climbing one cell. Items enter at belt height at the back and
-- leave at belt height one level up at the front. Like every belt it only gives its surface a
-- speed; the physics engine carries the items.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)

local Ramp = {}
local C = Kit.COLORS

local CELL = Config.CELL
local RUN = 2 * CELL
local ANGLE = math.atan2(CELL, RUN)
local LENGTH = math.sqrt(RUN * RUN + CELL * CELL)
-- Grippy enough that nothing slides back down: the slope needs more grip than a level belt.
local GRIP = PhysicalProperties.new(1, 2, 0, 100, 1)

-- The catalogue model's slope is a wedge, which the part converter can only draw as a block, so
-- the ramp is drawn here instead.
function Ramp.build(machine)
	local model, base = machine.model, machine.base
	local turn = CFrame.Angles(0, 0, ANGLE)
	local along = Vector3.new(math.cos(ANGLE), math.sin(ANGLE), 0)
	local up = Vector3.new(-math.sin(ANGLE), math.cos(ANGLE), 0)
	-- the middle of the surface: half-way along, half a cell above belt height
	local mid = Vector3.new(0, DeviceKit.BELT_TOP + CELL / 2, 0)

	local surface =
		Kit.conveyor(model, base, Vector3.new(LENGTH, 0.2, 2.35), mid - up * 0.1, along * Config.BELT_SPEED)
	surface.CFrame *= turn
	surface.CustomPhysicalProperties = GRIP

	local under = Kit.part(model, base, Vector3.new(LENGTH, 0.3, 2.9), mid - up * 0.35, C.dark)
	under.CFrame *= turn
	for _, z in { -1.3, 1.3 } do
		local rail = Kit.part(
			model,
			base,
			Vector3.new(LENGTH, 0.6, 0.25),
			mid + up * 0.1 + Vector3.new(0, 0, z),
			C.light
		)
		rail.CFrame *= turn
	end
	for step = -2, 2 do
		Kit.detail(
			model,
			base,
			Vector3.new(0.12, 0.03, 1.7),
			mid + along * (step * 1.2) + up * 0.01,
			C.mark,
			turn
		)
	end
	-- legs under the high half
	for _, x in { 0.45, 2.55 } do
		local top = mid.Y + x * CELL / RUN - 0.4
		local height = top + CELL / 2
		for _, z in { -1.08, 1.08 } do
			Kit.detail(
				model,
				base,
				Vector3.new(0.24, height, 0.24),
				Vector3.new(x, top - height / 2, z),
				C.mark
			)
		end
	end
end

return Ramp
