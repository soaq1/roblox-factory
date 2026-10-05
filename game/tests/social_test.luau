-- Runs outside Roblox:  lune run tests/social_test.luau
local T = require("./harness")
local SocialLogic = require("../src/shared/SocialLogic")

local test, eq = T.test, T.eq

local function facts(public: boolean, where: string)
	return {
		userId = 7,
		name = "kim",
		display = "김",
		public = public,
		where = where,
		host = "lee",
		hasIsland = true,
	}
end

-- Player cards
test("a public card says where the player is and offers a visit", function()
	local card = SocialLogic.card(facts(true, "own"))
	eq(card.private, false)
	eq(card.where, "own")
	eq(card.host, nil)
	eq(card.canVisit, true)
	eq(card.name, "kim")
	eq(card.userId, 7)
end)
test("a card names the host only when the player is on someone else's island", function()
	eq(SocialLogic.card(facts(true, "island")).host, "lee")
	eq(SocialLogic.card(facts(true, "away")).host, nil)
end)
test("a private card gives the name and nothing about where the player is", function()
	local card = SocialLogic.card(facts(false, "island"))
	eq(card.private, true)
	eq(card.name, "kim")
	eq(card.display, "김")
	eq(card.where, nil)
	eq(card.host, nil)
	eq(card.canVisit, false)
end)
test("a player whose island is not here cannot be visited from the card", function()
	local f = facts(true, "away")
	f.hasIsland = false
	eq(SocialLogic.card(f).canVisit, false)
end)
test("every card has a line of text for where the player is", function()
	for _, where in { "own", "island", "away" } do
		local line = SocialLogic.whereText(SocialLogic.card(facts(true, where)))
		assert(#line > 0, "no text for " .. where)
	end
	local private = SocialLogic.whereText(SocialLogic.card(facts(false, "own")))
	assert(string.find(private, "비공개"), "a private card should say it is private")
	assert(
		string.find(SocialLogic.whereText(SocialLogic.card(facts(true, "island"))), "lee"),
		"host not named"
	)
end)

-- Who is close enough to ask for a trade
test("the nearest player within range is chosen", function()
	local others =
		{ { id = 1, x = 9, y = 0, z = 0 }, { id = 2, x = 4, y = 0, z = 0 }, { id = 3, x = 0, y = 0, z = 30 } }
	eq(SocialLogic.nearest(0, 0, 0, others, 12), 2)
	eq(SocialLogic.nearest(0, 0, 28, others, 12), 3)
end)
test("nobody is chosen when everyone is too far, or there is nobody", function()
	eq(SocialLogic.nearest(0, 0, 0, { { id = 1, x = 13, y = 0, z = 0 } }, 12), nil)
	eq(SocialLogic.nearest(0, 0, 0, {}, 12), nil)
	-- exactly at the edge does not count
	eq(SocialLogic.nearest(0, 0, 0, { { id = 1, x = 12, y = 0, z = 0 } }, 12), nil)
end)
test("height counts as distance too", function()
	eq(SocialLogic.nearest(0, 0, 0, { { id = 1, x = 0, y = 20, z = 0 } }, 12), nil)
end)
test("two players equally far away always give the same answer", function()
	local a = { { id = 5, x = 3, y = 0, z = 0 }, { id = 2, x = -3, y = 0, z = 0 } }
	local b = { a[2], a[1] }
	eq(SocialLogic.nearest(0, 0, 0, a, 12), 2)
	eq(SocialLogic.nearest(0, 0, 0, b, 12), 2)
end)

-- Sign text
test("ordinary text goes on a sign unchanged", function()
	eq(SocialLogic.cleanSign("철 주괴 공장"), "철 주괴 공장")
	eq(SocialLogic.cleanSign("Iron -> this way"), "Iron -> this way")
end)
test("an empty sign is allowed, and blank edges are trimmed", function()
	eq(SocialLogic.cleanSign(""), "")
	eq(SocialLogic.cleanSign("   \n  "), "")
	eq(SocialLogic.cleanSign("  hello \n"), "hello")
end)
test("things that are not text are refused", function()
	eq(SocialLogic.cleanSign(nil), nil)
	eq(SocialLogic.cleanSign(42), nil)
	eq(SocialLogic.cleanSign({}), nil)
	eq(SocialLogic.cleanSign(string.rep("a", SocialLogic.SIGN_CHARS * 8 + 1)), nil)
	eq(SocialLogic.cleanSign("ab\255\254cd"), nil)
end)
test("a sign is cut to its limit of characters, counting Korean letters as one each", function()
	local long = string.rep("가", SocialLogic.SIGN_CHARS + 25)
	local cleaned = SocialLogic.cleanSign(long) :: string
	eq(utf8.len(cleaned), SocialLogic.SIGN_CHARS)
	-- the cut never lands in the middle of a letter
	assert(utf8.len(cleaned) ~= nil, "cut text is not valid")
	eq(
		SocialLogic.cleanSign(string.rep("가", SocialLogic.SIGN_CHARS)),
		string.rep("가", SocialLogic.SIGN_CHARS)
	)
end)
test("a sign keeps only its first few lines", function()
	local cleaned = SocialLogic.cleanSign("1\n2\n3\n4\n5\n6") :: string
	eq(#string.split(cleaned, "\n"), SocialLogic.SIGN_LINES)
	eq(string.sub(cleaned, 1, 3), "1\n2")
end)
test("control characters are dropped and line endings made uniform", function()
	eq(SocialLogic.cleanSign("a\tb\0c"), "abc")
	eq(SocialLogic.cleanSign("one\r\ntwo\rthree"), "one\ntwo\nthree")
end)

T.done()
