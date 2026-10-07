-- Loose items: real parts moved by the physics engine. Only the server makes or removes them.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local ModelBuilder = require(Shared.ModelBuilder)
local Stock = require(Shared.Stock)(Defs)

local ItemService = {}

local folder = Instance.new("Folder")
folder.Name = "Items"
folder.Parent = Workspace
ItemService.folder = folder

local PHYSICS = PhysicalProperties.new(1, 0.7, 0, 1, 1)
local REST_SPEED = 0.8 -- stacks only merge when both are nearly still, so items on a moving belt stay separate

local nextUid = 0
local queue: { BasePart } = {} -- oldest first, may contain parts that are already gone
local liveCount = 0

local overlap = OverlapParams.new()
overlap.FilterType = Enum.RaycastFilterType.Include
overlap.FilterDescendantsInstances = { folder }

local function isLive(part: Instance): boolean
	return part.Parent == folder and not part:GetAttribute("Dead")
end

local function kill(part: BasePart)
	if isLive(part) then
		part:SetAttribute("Dead", true)
		liveCount -= 1
		part:Destroy()
	end
end

local function refreshLabel(part: BasePart)
	local count = part:GetAttribute("Count") :: number
	local gui = part:FindFirstChild("Label") :: BillboardGui?
	if count <= 1 then
		if gui then
			gui:Destroy()
		end
		return
	end
	if not gui then
		local newGui = Instance.new("BillboardGui")
		newGui.Name = "Label"
		newGui.Size = UDim2.fromOffset(60, 22)
		newGui.StudsOffset = Vector3.new(0, 1.1, 0)
		newGui.MaxDistance = 70
		local text = Instance.new("TextLabel")
		text.Name = "Text"
		text.Size = UDim2.fromScale(1, 1)
		text.BackgroundTransparency = 1
		text.TextColor3 = Color3.new(1, 1, 1)
		text.TextStrokeTransparency = 0.3
		text.Font = Enum.Font.GothamBold
		text.TextSize = 16
		text.Parent = newGui
		newGui.Parent = part
		gui = newGui
	end
	local text = (gui :: BillboardGui):FindFirstChild("Text") :: TextLabel
	text.Text = "×" .. count
end

local function tryMerge(a: BasePart, b: BasePart)
	if not isLive(a) or not isLive(b) or a == b then
		return
	end
	if a:GetAttribute("ItemId") ~= b:GetAttribute("ItemId") then
		return
	end
	if a.AssemblyLinearVelocity.Magnitude > REST_SPEED or b.AssemblyLinearVelocity.Magnitude > REST_SPEED then
		return
	end
	local total = (a:GetAttribute("Count") :: number) + (b:GetAttribute("Count") :: number)
	if total > Config.MAX_STACK then
		return
	end
	-- The older stack survives, so two touching stacks always agree on who absorbs whom.
	local keep, gone = a, b
	if (b:GetAttribute("Uid") :: number) < (a:GetAttribute("Uid") :: number) then
		keep, gone = b, a
	end
	kill(gone)
	keep:SetAttribute("Count", total)
	refreshLabel(keep)
end

local function trim()
	while liveCount > Config.MAX_LOOSE_ITEMS and #queue > 0 do
		local oldest = table.remove(queue, 1) :: BasePart
		kill(oldest)
	end
	-- Drop entries for parts that were removed some other way, so the queue cannot grow without bound.
	if #queue > Config.MAX_LOOSE_ITEMS * 4 then
		local kept = {}
		for _, part in queue do
			if isLive(part) then
				table.insert(kept, part)
			end
		end
		queue = kept
	end
end

-- `itemId` is a bag key: an item, or "block:<id>" for a block that is only a block.
function ItemService.spawn(itemId: string, count: number, position: Vector3): BasePart?
	local def = Stock.loose(itemId)
	if not def or count < 1 then
		return nil
	end
	nextUid += 1
	local part = Instance.new("Part")
	part.Name = itemId
	part.Size = Vector3.new(def.size[1], def.size[2], def.size[3])
	part.Color = Color3.fromRGB(def.color[1], def.color[2], def.color[3])
	part.Material = Enum.Material.SmoothPlastic
	part.CustomPhysicalProperties = PHYSICS
	part.Position = position
	local source = ModelBuilder.template("i_" .. itemId)
	if source then
		-- The box does the colliding, because a plain box rides a belt predictably. What is seen
		-- is the item's own shape, fixed to the box and weighing nothing.
		part.Transparency = 1
		local look = source:Clone()
		look.Name = "Look"
		look.Anchored = false
		look.CanCollide = false
		look.CanQuery = false
		look.CanTouch = false
		look.Massless = true
		look.Material = Enum.Material.SmoothPlastic
		look.CFrame = part.CFrame * ModelBuilder.FIX
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = part
		weld.Part1 = look
		weld.Parent = look
		look.Parent = part
	elseif def.ball then
		-- Looks round, but still collides as a box: a real ball would roll, and a rolling ball
		-- travels along a belt at a fraction of the belt's speed.
		local round = Instance.new("SpecialMesh")
		round.MeshType = Enum.MeshType.Sphere
		round.Parent = part
	end
	part:SetAttribute("ItemId", itemId)
	part:SetAttribute("Count", math.min(count, Config.MAX_STACK))
	part:SetAttribute("Uid", nextUid)
	part.Parent = folder
	-- The server keeps physics ownership so a client cannot move or teleport items.
	pcall(function()
		part:SetNetworkOwner(nil)
	end)
	part.Touched:Connect(function(other)
		if other.Parent == folder then
			tryMerge(part, other)
		end
	end)
	part.Destroying:Connect(function()
		if not part:GetAttribute("Dead") then
			-- Removed by the engine (fell out of the world) rather than by kill().
			part:SetAttribute("Dead", true)
			liveCount -= 1
		end
	end)
	liveCount += 1
	table.insert(queue, part)
	refreshLabel(part)
	trim()
	return part
end

-- Spawns any amount, split into full stacks.
function ItemService.spawnMany(itemId: string, count: number, position: Vector3)
	local i = 0
	while count > 0 do
		local n = math.min(count, Config.MAX_STACK)
		ItemService.spawn(itemId, n, position + Vector3.new(0, i * 0.9, 0))
		count -= n
		i += 1
	end
end

function ItemService.info(part: Instance): (string?, number)
	if not isLive(part) then
		return nil, 0
	end
	return part:GetAttribute("ItemId") :: string, part:GetAttribute("Count") :: number
end

-- Removes up to n items from a stack and returns how many were removed.
function ItemService.take(part: BasePart, n: number): number
	local _, count = ItemService.info(part)
	local taken = math.min(n, count)
	if taken <= 0 then
		return 0
	end
	if taken >= count then
		kill(part)
	else
		part:SetAttribute("Count", count - taken)
		refreshLabel(part)
	end
	return taken
end

function ItemService.inBox(cframe: CFrame, size: Vector3): { BasePart }
	return Workspace:GetPartBoundsInBox(cframe, size, overlap)
end

function ItemService.nearest(position: Vector3, range: number): BasePart?
	local best: BasePart? = nil
	local bestDistance = range
	for _, part in Workspace:GetPartBoundsInRadius(position, range, overlap) do
		local distance = (part.Position - position).Magnitude
		if isLive(part) and distance <= bestDistance then
			best, bestDistance = part, distance
		end
	end
	return best
end

-- The stack a player standing at `position` picks up: the nearest one lying still, and only if
-- there is none, the nearest one on the move. A moving item is one riding a belt, and taking
-- those by accident would empty the player's own factory line.
function ItemService.pick(position: Vector3, range: number, stillOnly: boolean?): BasePart?
	local still: BasePart? = nil
	local stillDistance = range
	local moving: BasePart? = nil
	local movingDistance = range
	for _, part in Workspace:GetPartBoundsInRadius(position, range, overlap) do
		if isLive(part) then
			local distance = (part.Position - position).Magnitude
			if part.AssemblyLinearVelocity.Magnitude <= REST_SPEED then
				if distance <= stillDistance then
					still, stillDistance = part, distance
				end
			elseif distance <= movingDistance then
				moving, movingDistance = part, distance
			end
		end
	end
	return still or (if stillOnly then nil else moving)
end

-- Counts what is really there, which also corrects the running total if the engine removed anything.
-- Touched only fires at the moment two parts meet, when at least one is still moving. This sweep
-- catches stacks that have since come to rest side by side.
function ItemService.start()
	task.spawn(function()
		while true do
			task.wait(0.5)
			for _, child in folder:GetChildren() do
				if
					child:IsA("BasePart")
					and isLive(child)
					and child.AssemblyLinearVelocity.Magnitude <= REST_SPEED
				then
					local reach = child.Size + Vector3.new(0.15, 0.15, 0.15)
					for _, other in Workspace:GetPartBoundsInBox(child.CFrame, reach, overlap) do
						tryMerge(child, other)
						if not isLive(child) then
							break
						end
					end
				end
			end
		end
	end)
end

function ItemService.count(): number
	liveCount = #folder:GetChildren()
	return liveCount
end

function ItemService.clearWhere(keep: (BasePart) -> boolean)
	for _, child in folder:GetChildren() do
		if child:IsA("BasePart") and not keep(child) then
			kill(child)
		end
	end
end

return ItemService
