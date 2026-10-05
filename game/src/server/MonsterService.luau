-- The monster island: a place apart from the hub where slimes live. They come at anyone who gets
-- close and hurt on contact. Killing one sometimes gives a monster part, which an extractor needs.
-- Slimes are plain anchored models that the server moves itself; there is no physics involved.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local ToolLogic = require(Shared.ToolLogic)
local HubService = require(script.Parent.HubService)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)
local World = require(script.Parent.World)

local MonsterService = {}

-- All of these are placeholders to be tuned by play.
local COUNT = 8
local HEALTH = 30
local SPEED = 7 -- studs per second
local SIGHT = 30 -- how close a player must come to be chased
local LEASH = 46 -- slimes stay within this of the island's middle, which keeps the arrival point safe
local BITE = 10 -- health taken per bite
local BITE_RANGE = 3.8
local BITE_GAP = 1.0 -- seconds between bites from one slime
local RESPAWN = 12 -- seconds until a slain slime is back
local HIT_REACH = 14 -- how far away a player can be and still hit one
local HIT_GAP = 0.3 -- seconds between hits that count
local KNOCKBACK = 4 -- studs a slime is pushed back by a hit
local SIZE = 4 -- studs across a slime

local GROUND = HubService.GROUND
local CENTRE = World.MONSTER_ORIGIN
local FLOOR_Y = CENTRE.Y + GROUND

type Slime = {
	model: Model,
	label: TextLabel,
	home: Vector3,
	at: Vector3, -- where it is on the ground; its height is worked out when it is drawn
	hp: number,
	alive: boolean,
	bitAt: number,
	phase: number,
}

local folder: Folder
local slimes: { Slime } = {}
local byModel: { [Instance]: Slime } = {}
local lastHit: { [Player]: number } = {}

local function flat(v: Vector3): Vector3
	return Vector3.new(v.X, 0, v.Z)
end

-- Keeps a ground position within the leash of the island's middle.
local function leashed(position: Vector3): Vector3
	local offset = flat(position - CENTRE)
	if offset.Magnitude > LEASH then
		offset = offset.Unit * LEASH
	end
	return Vector3.new(CENTRE.X + offset.X, 0, CENTRE.Z + offset.Z)
end

local function draw(slime: Slime, facing: Vector3?, hop: number)
	local position = Vector3.new(slime.at.X, FLOOR_Y + SIZE / 2 + hop, slime.at.Z)
	if facing and facing.Magnitude > 0.01 then
		slime.model:PivotTo(CFrame.lookAt(position, position + facing))
	else
		slime.model:PivotTo(slime.model:GetPivot().Rotation + position)
	end
end

local function makeSlime(home: Vector3, phase: number): Slime
	local model = Instance.new("Model")
	model.Name = "Slime"
	model:SetAttribute("Monster", "slime")
	local body = Instance.new("Part")
	body.Name = "Body"
	body.Shape = Enum.PartType.Ball
	body.Anchored = true
	body.Size = Vector3.new(SIZE, SIZE, SIZE)
	body.Color = Color3.fromRGB(110, 200, 120)
	body.Material = Enum.Material.SmoothPlastic
	body.Transparency = 0.12
	body.Parent = model
	model.PrimaryPart = body
	-- two eyes on the side it faces (a part's front is its -Z)
	for _, x in { -0.75, 0.75 } do
		local eye = Instance.new("Part")
		eye.Shape = Enum.PartType.Ball
		eye.Anchored = true
		eye.CanCollide = false
		eye.CanQuery = false
		eye.CanTouch = false
		eye.Size = Vector3.new(0.55, 0.55, 0.55)
		eye.Color = Color3.fromRGB(30, 34, 32)
		eye.Material = Enum.Material.SmoothPlastic
		eye.CFrame = body.CFrame * CFrame.new(x, 0.5, -SIZE / 2 + 0.2)
		eye.Parent = model
	end
	local label = HubService.sign(body, "", SIZE / 2 + 1.2)
	label.TextSize = 15

	local slime: Slime = {
		model = model,
		label = label,
		home = home,
		at = home,
		hp = HEALTH,
		alive = true,
		bitAt = 0,
		phase = phase,
	}
	byModel[model] = slime
	return slime
end

local function showHealth(slime: Slime)
	slime.label.Text = "슬라임 " .. math.max(0, slime.hp) .. "/" .. HEALTH
end

local function revive(slime: Slime)
	slime.hp = HEALTH
	slime.at = slime.home
	slime.alive = true
	showHealth(slime)
	draw(slime, nil, 0)
	slime.model.Parent = folder
end

local function build()
	folder = Instance.new("Folder")
	folder.Name = "MonsterIsland"
	HubService.block(
		folder,
		Vector3.new(140, 3, 140),
		CFrame.new(CENTRE),
		Color3.fromRGB(78, 104, 82),
		Enum.Material.Grass
	)
	-- a few standing stones, so the place is not a bare slab
	for i = 1, 6 do
		local angle = i * math.pi / 3 + 0.4
		local height = 5 + (i % 3) * 3
		local at = CENTRE + Vector3.new(math.cos(angle) * 58, GROUND + height / 2, math.sin(angle) * 58 * 0.8)
		HubService.block(
			folder,
			Vector3.new(4, height, 4),
			CFrame.new(at) * CFrame.Angles(0, angle, 0),
			Color3.fromRGB(86, 84, 82),
			Enum.Material.Slate
		)
	end
	-- the way back stands behind where players arrive
	local back = CFrame.new(CENTRE + Vector3.new(0, GROUND, 64))
	HubService.portal(folder, back, "허브로", Color3.fromRGB(53, 184, 166), true, HubService.toHub)
	folder.Parent = Workspace

	for i = 1, COUNT do
		local angle = (i - 1) * 2 * math.pi / COUNT
		local radius = if i % 2 == 0 then 30 else 18
		local home = Vector3.new(CENTRE.X + math.cos(angle) * radius, 0, CENTRE.Z + math.sin(angle) * radius)
		local slime = makeSlime(home, i * 0.9)
		table.insert(slimes, slime)
		revive(slime)
	end
end

type Target = { root: BasePart, humanoid: Humanoid }

-- Everyone alive who is standing on or near this island.
local function targets(): { Target }
	local list = {}
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		if root and root:IsA("BasePart") and humanoid and humanoid.Health > 0 then
			if flat(root.Position - CENTRE).Magnitude < 110 and math.abs(root.Position.Y - FLOOR_Y) < 40 then
				table.insert(list, { root = root, humanoid = humanoid })
			end
		end
	end
	return list
end

local function step(dt: number)
	local near = targets()
	if #near == 0 then
		return -- nobody here: the slimes stay where they are
	end
	local now = os.clock()
	for _, slime in slimes do
		if not slime.alive then
			continue
		end
		-- the closest player it can see
		local prey: Target? = nil
		local preyDistance = SIGHT
		for _, target in near do
			local distance = flat(target.root.Position - slime.at).Magnitude
			if distance < preyDistance then
				prey, preyDistance = target, distance
			end
		end

		local goal = if prey then flat(prey.root.Position) else slime.home
		local toGoal = flat(goal - slime.at)
		local distance = toGoal.Magnitude
		local stop = if prey then 2.5 else 0.3
		local moving = distance > stop
		if moving then
			slime.at = leashed(slime.at + toGoal.Unit * math.min(SPEED * dt, distance - stop))
		end
		local hop = if moving then math.abs(math.sin(now * 5 + slime.phase)) * 1.1 else 0
		draw(slime, if distance > 0.05 then toGoal else nil, hop)

		if prey and now - slime.bitAt >= BITE_GAP then
			local offset = prey.root.Position - Vector3.new(slime.at.X, FLOOR_Y + SIZE / 2, slime.at.Z)
			if flat(offset).Magnitude < BITE_RANGE and math.abs(offset.Y) < 6 then
				slime.bitAt = now
				prey.humanoid:TakeDamage(BITE)
			end
		end
	end
end

local function onAttack(player: Player, target: any)
	if typeof(target) ~= "Instance" then
		return
	end
	local model = if target:IsA("Model") then target else target:FindFirstAncestorOfClass("Model")
	local slime = model and byModel[model]
	local island = IslandService.get(player)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not slime or not slime.alive or not island or not root or not root:IsA("BasePart") then
		return
	end
	if not humanoid or humanoid.Health <= 0 then
		return
	end
	local offset = flat(slime.at - root.Position)
	if offset.Magnitude > HIT_REACH then
		return
	end
	local now = os.clock()
	if now - (lastHit[player] or 0) < HIT_GAP then
		return
	end
	lastHit[player] = now

	slime.hp -= ToolLogic.damage(Profile.inHand(island)) -- the sword in the hand, or fists
	showHealth(slime)
	if slime.hp > 0 then
		if offset.Magnitude > 0.1 then
			slime.at = leashed(slime.at + offset.Unit * KNOCKBACK)
		end
		return
	end

	slime.alive = false
	slime.model.Parent = nil
	task.delay(RESPAWN, revive, slime)
	if ToolLogic.rollPart(math.random()) then
		Inventory.add(island.bag, "monster_part", 1)
		Profile.push(island)
		Profile.notify(
			player,
			Defs.name("monster_part")
				.. "을(를) 얻었습니다! 빈 추출기를 만드는 데 들어갑니다"
		)
	end
end

function MonsterService.start()
	build()
	RunService.Heartbeat:Connect(function(dt)
		local ok, err = pcall(step, dt)
		if not ok then
			warn("monsters failed: " .. tostring(err))
		end
	end)
	Net.get("WorldAct").OnServerEvent:Connect(function(player: Player, action: any, target: any)
		if action == "attack" and RateLimit.allow(player) then
			onAttack(player, target)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastHit[player] = nil
	end)
end

return MonsterService
