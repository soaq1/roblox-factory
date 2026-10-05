-- The hub's merchants. The rules live in shared/ShopLogic and the prices in shared/Prices; this
-- module checks that the player is standing at the merchant's counter and moves goods and coins.
-- Selling here is the only way to turn things into coins from the game itself: there is no
-- machine that sells for you.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared.Net)
local Prices = require(Shared.Prices)
local ShopLogic = require(Shared.ShopLogic)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)
local World = require(script.Parent.World)

local ShopService = {}

local Stock = Profile.Stock

-- Is the player standing close enough to this merchant? False until the hub has been built.
local function atCounter(player: Player, merchant: string): boolean
	local spot = World.merchantAt[merchant]
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if typeof(spot) ~= "Vector3" or not root or not root:IsA("BasePart") then
		return false
	end
	return (root.Position - spot).Magnitude <= World.MERCHANT_RANGE
end

local function explain(reason: string?, key: any): string
	if reason == "coins" then
		return "코인이 모자랍니다"
	elseif reason == "missing" then
		return "그만큼 가지고 있지 않습니다"
	elseif reason == "full" then
		return "더 받을 수 없습니다"
	elseif reason == "unknown" then
		return (if type(key) == "string" and Stock.isKey(key) then Stock.name(key) else "그 물건")
			.. "은(는) 이 상인이 다루지 않습니다"
	end
	return "개수가 올바르지 않습니다"
end

local function onAct(player: Player, merchant: any, action: any, key: any, n: any)
	if not RateLimit.allow(player) then
		return
	end
	if type(merchant) ~= "string" or (action ~= "buy" and action ~= "sell") then
		return
	end
	local list = if action == "buy" then Prices.sells[merchant] else Prices.buys[merchant]
	local island = IslandService.get(player)
	if not list or not island then
		return
	end
	if not atCounter(player, merchant) then
		Profile.notify(player, "상인 가까이에서만 거래할 수 있습니다")
		return
	end
	local ok, reason, coins
	if action == "buy" then
		ok, reason, coins = ShopLogic.buy(island.bag, island.coins, list, key, n)
	else
		ok, reason, coins = ShopLogic.sell(island.bag, island.coins, list, key, n)
	end
	if not ok then
		Profile.notify(player, explain(reason, key))
		return
	end
	local moved = math.abs(coins - island.coins)
	island.coins = coins
	Profile.push(island)
	Profile.notify(
		player,
		Stock.name(key)
			.. " "
			.. n
			.. "개를 "
			.. moved
			.. "코인에 "
			.. (if action == "buy" then "샀습니다" else "팔았습니다")
	)
end

function ShopService.start()
	Net.get("ShopAct").OnServerEvent:Connect(onAct)
end

return ShopService
