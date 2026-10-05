--!strict
-- Rules for what players see of each other and for what may be written on a sign. Nothing here
-- touches Roblox: the server gathers the facts and these functions decide what to do with them.
local SocialLogic = {}

SocialLogic.SIGN_CHARS = 80 -- most characters a sign holds (a placeholder)
SocialLogic.SIGN_LINES = 4 -- most lines a sign holds (a placeholder)

export type Facts = {
	userId: number,
	name: string,
	display: string,
	public: boolean, -- the player's own "profile public" setting
	where: string, -- "own" (on their own island), "island" (on someone else's) or "away"
	host: string?, -- whose island, when `where` is "island"
	hasIsland: boolean, -- their island is on this server, so it can be visited
}
export type Card = {
	userId: number,
	name: string,
	display: string,
	private: boolean,
	where: string?,
	host: string?,
	canVisit: boolean,
}

-- What one player is shown about another. A private profile gives the name and nothing else:
-- not where they are, and no way to go to their island from the card.
function SocialLogic.card(facts: Facts): Card
	if not facts.public then
		return {
			userId = facts.userId,
			name = facts.name,
			display = facts.display,
			private = true,
			canVisit = false,
		}
	end
	return {
		userId = facts.userId,
		name = facts.name,
		display = facts.display,
		private = false,
		where = facts.where,
		host = if facts.where == "island" then facts.host else nil,
		canVisit = facts.hasIsland,
	}
end

-- The line on a card saying where its player is.
function SocialLogic.whereText(card: Card): string
	if card.private then
		return "프로필을 비공개로 해 두었습니다"
	elseif card.where == "own" then
		return "지금 자기 섬에 있습니다"
	elseif card.where == "island" then
		return "지금 " .. (card.host or "다른 사람") .. "님의 섬에 있습니다"
	end
	return "지금 허브나 섬 밖에 있습니다"
end

export type Spot = { id: number, x: number, y: number, z: number }

-- The nearest of `others` within `range` of a point, or nil. Ties go to the lower id so the
-- answer does not flicker between two players standing equally far away.
function SocialLogic.nearest(x: number, y: number, z: number, others: { Spot }, range: number): number?
	local best: number? = nil
	local bestDistance = range * range
	for _, other in others do
		local dx, dy, dz = other.x - x, other.y - y, other.z - z
		local distance = dx * dx + dy * dy + dz * dz
		if distance < bestDistance or (distance == bestDistance and best ~= nil and other.id < best) then
			best = other.id
			bestDistance = distance
		end
	end
	return best
end

-- Makes typed text fit a sign: line breaks made uniform, control characters dropped, blank edges
-- trimmed, and no more than SIGN_LINES lines or SIGN_CHARS characters. Returns nil for anything
-- that is not text at all (wrong type, far too long, or broken encoding). An empty string is a
-- valid result: it wipes the sign.
function SocialLogic.cleanSign(raw: any): string?
	if type(raw) ~= "string" or #raw > SocialLogic.SIGN_CHARS * 8 then
		return nil
	end
	if not utf8.len(raw) then
		return nil
	end
	local text = string.gsub(raw, "\r\n?", "\n")
	text = string.gsub(text, "[%z\1-\9\11-\31\127]", "")
	text = string.gsub(text, "^%s+", "")
	text = string.gsub(text, "%s+$", "")

	local lines = string.split(text, "\n")
	local kept = {}
	for i = 1, math.min(#lines, SocialLogic.SIGN_LINES) do
		table.insert(kept, lines[i])
	end
	text = table.concat(kept, "\n")

	local length = utf8.len(text)
	if not length then
		return nil
	end
	if length > SocialLogic.SIGN_CHARS then
		-- utf8.offset gives the byte where character n starts; cut just before the one after the last kept.
		local cut = utf8.offset(text, SocialLogic.SIGN_CHARS + 1)
		if cut then
			text = string.sub(text, 1, cut - 1)
		end
		text = string.gsub(text, "%s+$", "")
	end
	return text
end

return SocialLogic
