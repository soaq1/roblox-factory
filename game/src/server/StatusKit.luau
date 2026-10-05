-- The lamp on top of a machine that says what it is doing, and the count of what it puts out.
-- The lamp is a glowing ball, so it can be read from much further away than the text label.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local RateLogic = require(Shared.RateLogic)
local StatusText = require(Shared.StatusText)
local Kit = require(script.Parent.MachineKit)

local StatusKit = {}

StatusKit.STUCK_SECONDS = 2 -- finished items unable to leave for this long count as a blocked exit

-- Adds the lamp and the output meter. `offset` moves the lamp from its usual place above the
-- middle of the machine (in the machine's own frame).
function StatusKit.attach(machine, offset: Vector3?)
	local top = Vector3.new(0, -Config.CELL / 2 + machine.def.height + 0.38, 0)
	local lamp = Kit.detail(
		machine.model,
		machine.base,
		Vector3.new(0.55, 0.55, 0.55),
		top + (offset or Vector3.zero),
		Color3.fromRGB(150, 150, 150)
	)
	lamp.Name = "StatusLamp"
	lamp.Shape = Enum.PartType.Ball
	lamp.Material = Enum.Material.Neon
	machine.lamp = lamp
	machine.status = ""
	machine.meter = RateLogic.new()
	machine.stuckFor = 0
end

-- Sets what the machine is doing; `colour` overrides the usual colour for that code.
function StatusKit.set(machine, code: string, colour: { number }?)
	if machine.status == code then
		return
	end
	machine.status = code
	local c = colour or StatusText.COLOR[code] or StatusText.COLOR.unset
	machine.lamp.Color = Color3.fromRGB(c[1], c[2], c[3])
end

-- Records that n finished things left the machine just now.
function StatusKit.count(machine, n: number)
	RateLogic.add(machine.meter, os.clock(), n)
end

function StatusKit.rate(machine): number
	return RateLogic.perMinute(machine.meter, os.clock())
end

-- Tracks whether finished items are failing to leave. Call each tick with whether there was
-- something to send and whether it went. Returns true once the exit has been blocked for a while.
function StatusKit.stuck(machine, hadOutput: boolean, left: boolean, dt: number): boolean
	if hadOutput and not left then
		machine.stuckFor += dt
	else
		machine.stuckFor = 0
	end
	return machine.stuckFor >= StatusKit.STUCK_SECONDS
end

-- Shows text on the machine's label, touching it only when the text changes.
function StatusKit.say(machine, text: string)
	if machine.shown ~= text then
		machine.shown = text
		machine.label.Text = text
	end
end

-- Makes a machine's label a little taller, for those that show several lines.
function StatusKit.roomy(label: TextLabel)
	local gui = label.Parent
	if gui and gui:IsA("BillboardGui") then
		gui.Size = UDim2.fromOffset(230, 100)
	end
end

return StatusKit
