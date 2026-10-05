-- The chute: two cells long, dropping one cell. Items enter at belt height one level up at the
-- back and leave at belt height at the front. It only goes downhill.
--
-- The slide is not left to gravity alone: a free slide down one cell would leave at several times
-- belt speed and throw items across the next belt. Its surface carries items down at a steady
-- pace instead, the same way a belt does.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)

local Chute = {}
local C = Kit.COLORS

local CELL = Config.CELL
local RUN = 2 * CELL
local ANGLE = math.atan2(CELL, RUN)
local LENGTH = math.sqrt(RUN * RUN + CELL * CELL)
local SLIDE_SPEED = 7 -- studs per second down the slope, a little quicker than a belt
local GRIP = PhysicalProperties.new(1, 2, 0, 100, 1)

function Chute.build(machine)
	local model, base = machine.model, machine.base
	local turn = CFrame.Angles(0, 0, -ANGLE)
	local along = Vector3.new(math.cos(ANGLE), -math.sin(ANGLE), 0)
	local up = Vector3.new(math.sin(ANGLE), math.cos(ANGLE), 0)
	local mid = Vector3.new(0, DeviceKit.BELT_TOP + CELL / 2, 0)

	local surface =
		Kit.conveyor(model, base, Vector3.new(LENGTH, 0.2, 2.35), mid - up * 0.1, along * SLIDE_SPEED)
	surface.CFrame *= turn
	surface.Color = C.light
	surface.CustomPhysicalProperties = GRIP
	-- the same width between its walls as a belt has between its rails
	for _, z in { -1.3, 1.3 } do
		local wall = Kit.part(
			model,
			base,
			Vector3.new(LENGTH, 0.9, 0.25),
			mid + up * 0.25 + Vector3.new(0, 0, z),
			C.mark
		)
		wall.CFrame *= turn
	end
	-- legs under the high half
	for _, x in { -2.55, -0.45 } do
		local top = mid.Y - x * CELL / RUN - 0.3
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

return Chute
