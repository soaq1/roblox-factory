-- What a machine is doing, in words and in a lamp colour (r, g, b). The codes come from
-- ProcessLogic.status and from the machines themselves; the server writes them on the machine and
-- the machine window shows the same words.
local StatusText = {}

StatusText.TEXT = {
	working = "작동 중",
	waiting = "재료 기다림",
	blocked = "출구 막힘",
	nofuel = "연료 없음",
	nopower = "전기 없음",
	halted = "신호로 멈춤",
	unset = "만들 것을 고르세요",
	full = "가득 참",
}

StatusText.COLOR = {
	working = { 120, 220, 140 }, -- green: running
	waiting = { 240, 190, 60 }, -- yellow: nothing wrong, nothing to do
	blocked = { 230, 90, 80 }, -- red: it needs the player
	nofuel = { 230, 90, 80 },
	nopower = { 230, 90, 80 },
	halted = { 110, 150, 230 }, -- blue: stopped on purpose
	unset = { 150, 150, 150 },
	full = { 240, 190, 60 }, -- yellow: it is waiting to be emptied
}

function StatusText.of(code: string): string
	return StatusText.TEXT[code] or ""
end

function StatusText.rate(perMinute: number): string
	return "분당 " .. perMinute .. "개"
end

return StatusText
