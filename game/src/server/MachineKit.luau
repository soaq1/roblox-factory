-- Shared pieces machines are assembled from.
-- A machine is built in its own frame: +X is forward (where things come out), Y is up, +Z is the
-- right-hand side, and the origin is the centre of its footprint at the height of a cell's centre.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local ModelBuilder = require(Shared.ModelBuilder)

local MachineKit = {}

local CELL = Config.CELL

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

MachineKit.COLORS = {
	light = rgb(228, 225, 219),
	dark = rgb(72, 70, 67),
	belt = rgb(43, 42, 41),
	mark = rgb(110, 107, 102),
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

-- The look of a catalogue model, built from basic parts.
function MachineKit.visual(model: Instance, base: CFrame, id: string): Folder?
	return ModelBuilder.build(model, base, id)
end

-- One unseen box the size of the machine. It is what players and items bump into, and what the
-- build cursor hits.
function MachineKit.body(machine): Part
	local def = machine.def
	local height = math.max(def.height, 1)
	local part = Instance.new("Part")
	part.Name = "Body"
	part.Anchored = true
	part.Transparency = 1
	part.CanCollide = not def.walkThrough
	part.Size = Vector3.new(def.sx * CELL - 0.1, height, def.sz * CELL - 0.1)
	part.CFrame = machine.base * CFrame.new(0, -CELL / 2 + height / 2, 0)
	part.Parent = machine.model
	machine.model:SetAttribute("Solid", true)
	return part
end

local SIDES = {
	E = Vector3.new(1, 0, 0),
	W = Vector3.new(-1, 0, 0),
	S = Vector3.new(0, 0, 1),
	N = Vector3.new(0, 0, -1),
}

export type Port = { kind: string, box: CFrame, size: Vector3, spawn: Vector3 }

-- Where things enter and leave. `box` is the space just outside a mouth: for an input, an item
-- resting there is taken in; for an output, it must be empty before the next item comes out.
function MachineKit.ports(machine): { Port }
	local def = machine.def
	local ports = {}
	for _, port in def.ports do
		local outward = SIDES[port.side]
		local alongX = port.side == "E" or port.side == "W"
		local half = (if alongX then def.sx else def.sz) * CELL / 2
		local lateral = if alongX
			then Vector3.new(0, 0, -port.off * CELL)
			else Vector3.new(port.off * CELL, 0, 0)
		local edge = outward * half + lateral
		-- An input takes only what is pressed up against the mouth: the thin strip between the
		-- machine and where the side rail of a belt running past would be. So a belt that ends at
		-- the mouth feeds the machine, and a belt that passes by it does not.
		-- An output looks further out, so it waits for a gap before putting the next item down.
		local depth = if port.kind == "in" then 0.3 else 0.9
		table.insert(ports, {
			kind = port.kind,
			-- from the ground up to a little above belt height
			box = machine.base * CFrame.new(edge + outward * (depth / 2) + Vector3.new(0, -0.55, 0)),
			size = if alongX then Vector3.new(depth, 1.9, 2.2) else Vector3.new(2.2, 1.9, depth),
			spawn = (machine.base * CFrame.new(edge + outward * 0.75 + Vector3.new(0, -0.15, 0))).Position,
		})
	end
	return ports
end

function MachineKit.inputs(ports: { Port }): { Port }
	local list = {}
	for _, port in ports do
		if port.kind == "in" then
			table.insert(list, port)
		end
	end
	return list
end

function MachineKit.outputs(ports: { Port }): { Port }
	local list = {}
	for _, port in ports do
		if port.kind == "out" then
			table.insert(list, port)
		end
	end
	return list
end

-- A "press F" prompt on a machine. `run` gets the player who pressed it.
function MachineKit.prompt(machine, part: BasePart, action: string, run: (Player) -> ()): ProximityPrompt
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = action
	prompt.ObjectText = machine.def.name
	prompt.KeyboardKeyCode = Enum.KeyCode.F
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Parent = part
	prompt.Triggered:Connect(run)
	return prompt
end

-- A small read-out above the machine, visible from close by.
function MachineKit.label(part: BasePart, height: number): TextLabel
	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(190, 70)
	gui.StudsOffsetWorldSpace = Vector3.new(0, height / 2 + 1.2, 0)
	gui.MaxDistance = 30
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0.3
	label.Font = Enum.Font.GothamMedium
	label.TextSize = 14
	label.TextYAlignment = Enum.TextYAlignment.Bottom
	label.Text = ""
	label.Parent = gui
	gui.Parent = part
	return label
end

return MachineKit
