-- Going to other players' islands on this server, and home again. A visitor can look around and
-- use vending machines; building is refused elsewhere because every edit is made on the editor's
-- own island.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared.Net)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)

local VisitService = {}

-- Whose island each player was last sent to. Nil means their own.
local visiting: { [Player]: Player } = {}

local function list(player: Player)
	local islands = {}
	for owner in IslandService.all() do
		table.insert(islands, { userId = owner.UserId, name = owner.DisplayName, user = owner.Name })
	end
	table.sort(islands, function(a, b)
		return a.user < b.user
	end)
	local host = visiting[player]
	Net.get("Visit")
		:FireClient(player, { islands = islands, at = if host then host.UserId else player.UserId })
end

local function listForAll()
	for player in IslandService.all() do
		list(player)
	end
end

-- Puts a player on an island's arrival pad. Returns false if they have no body to move.
local function send(player: Player, island): boolean
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not character or not root or not root:IsA("BasePart") then
		return false
	end
	character:PivotTo(IslandService.spawnCFrame(island))
	root.AssemblyLinearVelocity = Vector3.zero
	return true
end

local function goHome(player: Player)
	local island = IslandService.get(player)
	if island and send(player, island) then
		visiting[player] = nil
		list(player)
	end
end

local function go(player: Player, userId: any)
	if type(userId) ~= "number" then
		return
	end
	local island = IslandService.byUserId(userId)
	if not island then
		Profile.notify(player, "그 섬은 지금 이 서버에 없습니다")
		list(player)
		return
	end
	if island.owner == player then
		goHome(player)
		return
	end
	if send(player, island) then
		visiting[player] = island.owner
		Profile.notify(
			player,
			island.owner.DisplayName .. "님의 섬에 왔습니다. V를 눌러 돌아갈 수 있습니다"
		)
		list(player)
	end
end

local function onAct(player: Player, action: any, userId: any)
	if not RateLimit.allow(player) or not IslandService.get(player) then
		return
	end
	if action == "list" then
		list(player)
	elseif action == "go" then
		go(player, userId)
	elseif action == "home" then
		goHome(player)
	end
end

function VisitService.start()
	Net.get("VisitAct").OnServerEvent:Connect(onAct)
	-- A new island takes a moment to appear after its owner joins.
	IslandService.onCreated(function()
		listForAll()
	end)
	Players.PlayerRemoving:Connect(function(player)
		visiting[player] = nil
		-- Anyone standing on the island that is about to go is sent home first.
		local leaving = IslandService.get(player)
		for visitor, host in visiting do
			if host == player then
				visiting[visitor] = nil
				local character = visitor.Character
				local root = character and character:FindFirstChild("HumanoidRootPart")
				if
					leaving
					and root
					and root:IsA("BasePart")
					and IslandService.owns(leaving, root.Position)
				then
					goHome(visitor)
				end
			end
		end
		task.defer(listForAll)
	end)
end

return VisitService
