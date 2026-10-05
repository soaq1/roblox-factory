-- Shared pieces machines are assembled from. Stand-in shapes until the real models are imported.
-- A machine is built in its own frame: +X is forward (where things come out), Y is up,
-- and the origin is the centre of its cell.
local MachineKit = {}

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

MachineKit.COLORS = {
	body = rgb(194, 190, 183),
	light = rgb(228, 225, 219),
	mid = rgb(143, 139, 133),
	dark = rgb(72, 70, 67),
	belt = rgb(43, 42, 41),
	mark = rgb(110, 107, 102),
	hole = rgb(20, 21, 22),
	inPort = rgb(240, 180, 41),
	outPort = rgb(53, 184, 166),
	glow = rgb(255, 90, 31),
	wood = rgb(201, 156, 97),
	woodDark = rgb(168, 125, 71),
}
local C = MachineKit.COLORS

function MachineKit.base(center: Vector3, dir: number): CFrame
	return CFrame.new(center) * CFrame.Angles(0, -dir * math.pi / 2, 0)
end

function MachineKit.part(model: Instance, base: CFrame, size: Vector3, offset: Vector3, color: Color3): Part
	local part = Instance.new("Part")
	part.Anchored = true
	part.Size = size
	part.CFrame = base * CFrame.new(offset)
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.Parent = model
	return part
end

-- A surface that carries whatever rests on it. `velocity` is in the machine's own frame.
function MachineKit.conveyor(
	model: Instance,
	base: CFrame,
	size: Vector3,
	offset: Vector3,
	velocity: Vector3
): Part
	local part = MachineKit.part(model, base, size, offset, C.belt)
	part.Name = "Conveyor"
	part.AssemblyLinearVelocity = base:VectorToWorldSpace(velocity)
	return part
end

-- Decoration that nothing bumps into and the build cursor ignores.
function MachineKit.detail(
	model: Instance,
	base: CFrame,
	size: Vector3,
	offset: Vector3,
	color: Color3,
	turn: CFrame?
): Part
	local part = MachineKit.part(model, base, size, offset, color)
	if turn then
		part.CFrame *= turn
	end
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	return part
end

-- The short belt at a machine's mouth. `x` is where it sits along the machine; it always pushes forward.
function MachineKit.lip(model: Instance, base: CFrame, x: number, length: number, speed: number): Part
	MachineKit.part(model, base, Vector3.new(length, 0.6, 2.7), Vector3.new(x, -1.2, 0), C.dark)
	for _, z in { -1.3, 1.3 } do
		MachineKit.part(model, base, Vector3.new(length, 0.6, 0.25), Vector3.new(x, -0.6, z), C.light)
	end
	return MachineKit.conveyor(
		model,
		base,
		Vector3.new(length, 0.2, 2.35),
		Vector3.new(x, -0.8, 0),
		Vector3.new(speed, 0, 0)
	)
end

-- The coloured bar and dark opening that mark a mouth. Yellow is in, teal is out.
function MachineKit.mouth(model: Instance, base: CFrame, x: number, isInput: boolean)
	local out = if x >= 0 then 0.03 else -0.03
	MachineKit.detail(model, base, Vector3.new(0.06, 0.9, 2.2), Vector3.new(x + out, -0.25, 0), C.hole)
	MachineKit.detail(
		model,
		base,
		Vector3.new(0.08, 0.28, 2.3),
		Vector3.new(x + out, 0.38, 0),
		if isInput then C.inPort else C.outPort
	)
end

return MachineKit
