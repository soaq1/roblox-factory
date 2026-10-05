-- Trades between two players on the same server. The rules live in shared/TradeLogic; this module
-- pairs players up, feeds their requests in, and moves the goods when both have agreed.
-- One player asks; the trade opens when the other asks back.
-- What the "Trade" channel sends a client:
--   { request = { id, name } }   someone has asked this player to trade
--   { withdrawn = id }           that request is gone
--   { you, a, b }                the open trade as it stands; `you` is "a" or "b"
--   nil                          the trade has closed
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared.Net)
local ToolLogic = require(Shared.ToolLogic)
local TradeLogic = require(Shared.TradeLogic)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)

local TradeService = {}

local Stock = Profile.Stock

type Open = { session: TradeLogic.Session, a: Player, b: Player }

local asked: { [Player]: Player } = {} -- who each player has asked
local open: { [Player]: Open } = {}

local function whoIn(trade: Open, player: Player): string
	return if trade.a == player then "a" else "b"
end

-- Shows both players where the trade stands. Each is also told which side they are.
local function show(trade: Open)
	local s = trade.session
	for _, player in { trade.a, trade.b } do
		Net.get("Trade"):FireClient(player, {
			you = whoIn(trade, player),
			a = { name = trade.a.Name, offer = s.a.offer, coins = s.a.coins, ready = s.a.ready },
			b = { name = trade.b.Name, offer = s.b.offer, coins = s.b.coins, ready = s.b.ready },
		})
	end
end

local function close(trade: Open, message: string?)
	for _, player in { trade.a, trade.b } do
		if open[player] == trade then
			open[player] = nil
		end
		if player.Parent then
			Net.get("Trade"):FireClient(player, nil)
			if message then
				Profile.notify(player, message)
			end
		end
	end
end

local function finish(trade: Open)
	local islandA, islandB = IslandService.get(trade.a), IslandService.get(trade.b)
	if not islandA or not islandB then
		close(trade, "거래가 취소되었습니다")
		return
	end
	local ok, reason, coinsA, coinsB =
		TradeLogic.complete(trade.session, islandA.bag, islandA.coins, islandB.bag, islandB.coins)
	if ok then
		islandA.coins, islandB.coins = coinsA, coinsB
		Profile.push(islandA)
		Profile.push(islandB)
		close(trade, "거래가 끝났습니다")
	elseif reason == "full" then
		show(trade)
		Profile.notify(trade.a, "받는 쪽 가방이나 지갑이 넘칩니다")
		Profile.notify(trade.b, "받는 쪽 가방이나 지갑이 넘칩니다")
	else
		show(trade)
		Profile.notify(trade.a, "내놓은 것이 바뀌어 다시 확인이 필요합니다")
		Profile.notify(trade.b, "내놓은 것이 바뀌어 다시 확인이 필요합니다")
	end
end

function TradeService.ask(player: Player, target: any)
	if typeof(target) ~= "Instance" or not target:IsA("Player") or target == player then
		return
	end
	if not IslandService.get(player) or not IslandService.get(target) then
		return
	end
	if open[player] or open[target] then
		Profile.notify(player, "이미 거래 중입니다")
		return
	end
	if asked[target] == player then
		-- Accepting: anything this player had asked of someone else no longer stands.
		local other = asked[player]
		if other and other ~= target and other.Parent then
			Net.get("Trade"):FireClient(other, { withdrawn = player.UserId })
		end
		asked[target] = nil
		asked[player] = nil
		local trade: Open = { session = TradeLogic.new(), a = target, b = player }
		open[player] = trade
		open[target] = trade
		show(trade)
		return
	end
	if asked[player] == target then
		-- Asking again (T pressed twice beside them) does not pester the other player again.
		Profile.notify(player, target.Name .. "님의 대답을 기다리는 중입니다")
		return
	end
	local before = asked[player]
	if before and before.Parent then
		-- Only one request stands at a time: the earlier one is taken back.
		Net.get("Trade"):FireClient(before, { withdrawn = player.UserId })
	end
	asked[player] = target
	Profile.notify(player, target.Name .. "님에게 거래를 청했습니다")
	Profile.notify(
		target,
		player.Name
			.. "님이 거래를 청했습니다. 가까이 가서 T를 누르거나 거래 화면에서 받을 수 있습니다"
	)
	-- The trade screen shows this as a request waiting to be accepted.
	Net.get("Trade"):FireClient(target, { request = { id = player.UserId, name = player.Name } })
end

function TradeService.offer(player: Player, key: any, n: any)
	local trade, island = open[player], IslandService.get(player)
	if not trade or not island or not Stock.isKey(key) then
		return
	end
	-- The last tool is not traded away, for the same reason it is not dropped.
	if ToolLogic.parse(key) and type(n) == "number" and n >= ToolLogic.count(island.bag) then
		Profile.notify(player, "마지막 도구는 거래에 올릴 수 없습니다")
		return
	end
	local ok, reason = TradeLogic.setOffer(trade.session, whoIn(trade, player), key, n, island.bag)
	if ok then
		show(trade)
	else
		Profile.notify(
			player,
			if reason == "missing"
				then "그만큼 가지고 있지 않습니다"
				else "올릴 수 없습니다"
		)
	end
end

function TradeService.coins(player: Player, n: any)
	local trade, island = open[player], IslandService.get(player)
	if not trade or not island then
		return
	end
	local ok, reason = TradeLogic.setCoins(trade.session, whoIn(trade, player), n, island.coins)
	if ok then
		show(trade)
	else
		Profile.notify(
			player,
			if reason == "missing" then "코인이 모자랍니다" else "올릴 수 없습니다"
		)
	end
end

function TradeService.ready(player: Player, ready: any)
	local trade = open[player]
	if not trade or not TradeLogic.setReady(trade.session, whoIn(trade, player), ready) then
		return
	end
	if TradeLogic.isAgreed(trade.session) then
		finish(trade)
	else
		show(trade)
	end
end

function TradeService.cancel(player: Player)
	local target = asked[player]
	asked[player] = nil
	if target and target.Parent then
		Net.get("Trade"):FireClient(target, { withdrawn = player.UserId })
	end
	local trade = open[player]
	if trade then
		close(trade, player.Name .. "님이 거래를 취소했습니다")
	end
end

function TradeService.start()
	local actions = {
		ask = TradeService.ask,
		offer = TradeService.offer,
		coins = TradeService.coins,
		ready = TradeService.ready,
		cancel = TradeService.cancel,
	}
	Net.get("TradeAct").OnServerEvent:Connect(function(player: Player, action: any, a: any, b: any)
		local run = type(action) == "string" and actions[action]
		if run and RateLimit.allow(player) then
			run(player, a, b)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		for asker, target in asked do
			if asker == player or target == player then
				asked[asker] = nil
				if asker == player and target.Parent then
					Net.get("Trade"):FireClient(target, { withdrawn = player.UserId })
				end
			end
		end
		local trade = open[player]
		if trade then
			close(trade, "상대가 나가서 거래가 취소되었습니다")
		end
	end)
end

return TradeService
