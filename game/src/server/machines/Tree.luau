-- A tree: one thing that stands on the island, not a pile of blocks. Its shape comes from a seed
-- (shared/TreeGen), so no two are quite alike and each looks the same after a save and load.
-- An axe brings the whole tree down at once; it leaves logs and a sapling or two, and no stump.
-- It keeps the cells its trunk and leaves fill, so nothing can be built into it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local ModelBuilder = require(Shared.ModelBuilder)
local TreeGen = require(Shared.TreeGen)

local Tree = {}

local CELL = Config.CELL
local BARK = Color3.fromRGB(111, 76, 48)
local LEAVES = { Color3.fromRGB(47, 125, 51), Color3.fromRGB(60, 149, 57), Color3.fromRGB(87, 178, 70) }
local FALL_SECONDS = 0.9

-- The cells a tree at this cell would keep, and the state it is built from. A new tree gets a
-- seed of its own here; a saved one brings its seed with it. MachineService calls this before
-- anything is made, and makes nothing if any of the cells is taken.
function Tree.claim(x: number, y: number, z: number, saved: any): ({ { number } }, any)
	local state = { seed = math.random(1, 2 ^ 30), giant = false }
	if type(saved) == "table" then
		if type(saved.seed) == "number" and saved.seed == saved.seed then
			state.seed = math.clamp(math.floor(saved.seed), 1, 2 ^ 30)
		end
		state.giant = saved.giant == true
	end
	local cells = {}
	for _, step in TreeGen.make(state.seed, state.giant).cells do
		table.insert(cells, { x + step[1], y + step[2], z + step[3] })
	end
	return cells, state
end

local function piece(parent: Instance, solid: boolean): Part
	local part = Instance.new("Part")
	part.Anchored = true
	part.Material = Enum.Material.SmoothPlastic
	part.CanCollide = solid
	part.CanQuery = solid
	part.CanTouch = false
	part.CastShadow = solid
	part.Parent = parent
	return part
end

-- A copy of an imported mesh set up like `piece`.
local function dress(source: MeshPart, parent: Instance, solid: boolean): BasePart
	local part = source:Clone()
	part.Anchored = true
	part.Material = Enum.Material.SmoothPlastic
	part.CanCollide = solid
	part.CanQuery = solid
	part.CanTouch = false
	part.CastShadow = true
	part.Parent = parent
	return part
end

function Tree.build(machine)
	machine.model:SetAttribute("Solid", true)
end

-- A tree is always made with its state (see claim), so the building happens here.
function Tree.load(machine, saved)
	local tree = TreeGen.make(saved.seed, saved.giant)
	machine.tree = tree
	machine.state = { seed = saved.seed, giant = saved.giant == true }
	-- the middle of the ground under the trunk
	local foot = machine.center - Vector3.new(0, CELL / 2, 0)
	local visual = Instance.new("Folder")
	visual.Name = "Visual"

	local stick = ModelBuilder.template("t_limb")
	for _, limb in tree.limbs do
		local a = foot + Vector3.new(limb.ax, limb.ay, limb.az)
		local b = foot + Vector3.new(limb.bx, limb.by, limb.bz)
		local length = (b - a).Magnitude + limb.r * 0.6
		-- a cylinder, and the stick mesh as modelled, lie along their own X
		local along = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0)
		local part: BasePart
		if stick then
			-- a six-sided stick, a little thinner at the far end
			part = dress(stick, visual, limb.trunk)
			part.Size = stick.Size * Vector3.new(length, limb.r * 2.2, limb.r * 2.2)
			part.CFrame = along * ModelBuilder.FIX
		else
			local round = piece(visual, limb.trunk)
			round.Shape = Enum.PartType.Cylinder
			round.Size = Vector3.new(length, limb.r * 2, limb.r * 2)
			round.CFrame = along
			part = round
		end
		part.Name = if limb.trunk then "Trunk" else "Branch"
		part.Color = BARK
	end
	for _, lump in tree.lumps do
		local turned = CFrame.new(foot + Vector3.new(lump.x, lump.y, lump.z))
			* CFrame.Angles(lump.rx, lump.ry, lump.rz)
		local blob = ModelBuilder.template("t_leaf" .. lump.shade)
		local part: BasePart
		if blob then
			-- a lumpy faceted ball, stretched to the size of this mass of leaves
			part = dress(blob, visual, false)
			part.Size = blob.Size * Vector3.new(lump.sx, lump.sy, lump.sz) * 1.15
		else
			part = piece(visual, false)
			part.Size = Vector3.new(lump.sx, lump.sy, lump.sz)
		end
		part.CFrame = turned
		part.Name = "Leaves"
		part.Color = LEAVES[lump.shade]
	end
	visual.Parent = machine.model
	machine.visual = visual
end

function Tree.save(machine)
	return machine.state
end

-- How hard this tree is to bring down. An axe is the tool for it.
function Tree.hardness(machine): number
	return if machine.tree then machine.tree.hardness else 12
end

-- What comes from felling it. Asking for this is what marks the tree as felled, as opposed to
-- being cleared away with its island.
function Tree.drops(machine): { [string]: number }
	machine.felled = true
	local logs = if machine.tree then machine.tree.logs else 5
	return { log = logs, sapling = TreeGen.saplings(math.random()) }
end

-- Called as the tree is taken off the island. A felled tree tips over and is gone; a tree that
-- goes with its island just goes.
function Tree.removed(machine)
	local visual = machine.visual
	if not machine.felled or not visual then
		return
	end
	visual.Parent = Workspace
	local foot = CFrame.new(machine.center - Vector3.new(0, CELL / 2, 0))
		* CFrame.Angles(0, math.random() * math.pi * 2, 0)
	local parts: { [BasePart]: CFrame } = {}
	for _, part in visual:GetChildren() do
		if part:IsA("BasePart") then
			part.CanCollide = false
			part.CanQuery = false
			parts[part] = foot:ToObjectSpace(part.CFrame)
		end
	end
	local elapsed = 0
	local connection: RBXScriptConnection
	connection = RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		local t = math.min(elapsed / FALL_SECONDS, 1)
		-- slow at first, then faster, like something toppling
		local tipped = foot * CFrame.Angles(0, 0, -math.rad(86) * t * t)
		for part, offset in parts do
			part.CFrame = tipped * offset
		end
		if t >= 1 then
			connection:Disconnect()
			visual:Destroy()
		end
	end)
end

return Tree
