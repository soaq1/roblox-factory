--!strict
-- A trade between two players, "a" and "b". Each puts up items and coins and then marks themselves
-- ready. Changing anything un-readies both, so nobody can swap an offer after the other agreed.
-- Nothing moves until `complete`, which checks both sides again and then swaps everything at once.
local TradeLogic = {}

export type Bag = { [string]: number }
export type Side = { offer: Bag, coins: number, ready: boolean }
export type Session = { a: Side, b: Side, done: boolean }

TradeLogic.MAX_KINDS = 24 -- different things one side can put up
local LIMIT = 2 ^ 31
local MAX_COINS = 10 ^ 15

local function side(session: Session, who: any): Side?
	if who == "a" then
		return session.a
	elseif who == "b" then
		return session.b
	end
	return nil
end

local function unready(session: Session)
	session.a.ready = false
	session.b.ready = false
end

local function isWhole(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= 0
end

function TradeLogic.new(): Session
	return {
		a = { offer = {}, coins = 0, ready = false },
		b = { offer = {}, coins = 0, ready = false },
		done = false,
	}
end

-- Sets how many of one thing a side puts up. Zero takes it off the table.
function TradeLogic.setOffer(session: Session, who: any, key: any, n: any, bag: Bag): (boolean, string?)
	local mine = side(session, who)
	if not mine or session.done then
		return false, "closed"
	end
	if type(key) ~= "string" or not isWhole(n) then
		return false, "amount"
	end
	if n > (bag[key] or 0) then
		return false, "missing"
	end
	if n > 0 and not mine.offer[key] then
		local kinds = 0
		for _ in mine.offer do
			kinds += 1
		end
		if kinds >= TradeLogic.MAX_KINDS then
			return false, "kinds"
		end
	end
	if n > 0 then
		mine.offer[key] = n
	else
		mine.offer[key] = nil
	end
	unready(session)
	return true, nil
end

function TradeLogic.setCoins(session: Session, who: any, n: any, balance: number): (boolean, string?)
	local mine = side(session, who)
	if not mine or session.done then
		return false, "closed"
	end
	if not isWhole(n) or n > MAX_COINS then
		return false, "amount"
	end
	if n > balance then
		return false, "missing"
	end
	mine.coins = n
	unready(session)
	return true, nil
end

function TradeLogic.setReady(session: Session, who: any, ready: any): boolean
	local mine = side(session, who)
	if not mine or session.done or type(ready) ~= "boolean" then
		return false
	end
	mine.ready = ready
	return true
end

function TradeLogic.isAgreed(session: Session): boolean
	return not session.done and session.a.ready and session.b.ready
end

local function holds(bag: Bag, balance: number, mine: Side): boolean
	if mine.coins > balance then
		return false
	end
	for key, n in mine.offer do
		if (bag[key] or 0) < n then
			return false
		end
	end
	return true
end

-- Would this bag overflow after giving `out` and receiving `inc`?
local function fits(bag: Bag, out: Bag, inc: Bag): boolean
	for key, n in inc do
		if (bag[key] or 0) - (out[key] or 0) + n >= LIMIT then
			return false
		end
	end
	return true
end

local function takeOut(bag: Bag, offer: Bag)
	for key, n in offer do
		local left = (bag[key] or 0) - n
		if left > 0 then
			bag[key] = left
		else
			bag[key] = nil
		end
	end
end

local function putIn(bag: Bag, offer: Bag)
	for key, n in offer do
		bag[key] = (bag[key] or 0) + n
	end
end

-- Swaps everything, if both are ready and both still hold what they put up. Returns the two new
-- coin balances. On failure nothing has moved; if what a side holds has changed since they
-- agreed, both are un-readied so they look again.
function TradeLogic.complete(
	session: Session,
	bagA: Bag,
	coinsA: number,
	bagB: Bag,
	coinsB: number
): (boolean, string?, number, number)
	if not TradeLogic.isAgreed(session) then
		return false, "unready", coinsA, coinsB
	end
	local a, b = session.a, session.b
	if not holds(bagA, coinsA, a) or not holds(bagB, coinsB, b) then
		unready(session)
		return false, "changed", coinsA, coinsB
	end
	local afterA = coinsA - a.coins + b.coins
	local afterB = coinsB - b.coins + a.coins
	if
		afterA > MAX_COINS
		or afterB > MAX_COINS
		or not fits(bagA, a.offer, b.offer)
		or not fits(bagB, b.offer, a.offer)
	then
		unready(session)
		return false, "full", coinsA, coinsB
	end
	-- Take both offers out before putting either in, so the same thing passing both ways is right.
	takeOut(bagA, a.offer)
	takeOut(bagB, b.offer)
	putIn(bagB, a.offer)
	putIn(bagA, b.offer)
	session.done = true
	return true, nil, afterA, afterB
end

return TradeLogic
