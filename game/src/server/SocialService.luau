-- What players may learn about each other. A client asks about a player (by clicking on them) and
-- is sent a card; how much the card says is up to the player it is about, through their
-- "profile public" setting. Asking someone to trade goes through TradeService, not here.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared.Net)
local SocialLogic = require(Shared.SocialLogic)
local IslandService = require(script.Parent.IslandService)
local PrefsService = require(script.Parent.PrefsService)
local RateLimit = require(script.Parent.RateLimit)

local SocialService = {}

-- Where a player is standing, in the card's terms, and whose island if it is someone else's.
local function whereIs(target: Player): (string, string?)
	local character = target.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return "away", nil
	end
	local island = IslandService.at(root.Position)
	if not island then
		return "away", nil
	elseif island.owner == target then
		return "own", nil
	end
	return "island", island.owner.DisplayName
end

local function sendCard(player: Player, target: any)
	if typeof(target) ~= "Instance" or not target:IsA("Player") or target == player then
		return
	end
	-- Both have to be properly in the game: a player still loading has no settings to respect yet.
	if not IslandService.get(player) or not IslandService.get(target) then
		return
	end
	local where, host = whereIs(target)
	local card = SocialLogic.card({
		userId = target.UserId,
		name = target.Name,
		display = target.DisplayName,
		public = PrefsService.setting(target, "profilePublic"),
		where = where,
		host = host,
		hasIsland = IslandService.get(target) ~= nil,
	})
	Net.get("PlayerInfo"):FireClient(player, card)
end

function SocialService.start()
	Net.get("PlayerAct").OnServerEvent:Connect(function(player: Player, action: any, target: any)
		if action == "info" and RateLimit.allow(player) then
			sendCard(player, target)
		end
	end)
end

return SocialService
