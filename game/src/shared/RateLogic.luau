--!strict
-- Counts what actually left a machine and says how many that was over the last minute. It is
-- measured, not worked out from the recipe: a blocked line shows as a falling number.
local RateLogic = {}

RateLogic.WINDOW = 60 -- seconds looked back over
RateLogic.BUCKET = 5 -- seconds lumped together

export type Meter = { buckets: { [number]: number } }

function RateLogic.new(): Meter
	return { buckets = {} }
end

local function slot(now: number): number
	return math.floor(now / RateLogic.BUCKET)
end

-- Forgets everything older than the window.
local function prune(meter: Meter, now: number)
	local oldest = slot(now) - RateLogic.WINDOW / RateLogic.BUCKET
	for index in meter.buckets do
		if index <= oldest then
			meter.buckets[index] = nil
		end
	end
end

-- Records that n things left at time `now` (seconds on any steady clock).
function RateLogic.add(meter: Meter, now: number, n: number)
	if n <= 0 then
		return
	end
	prune(meter, now)
	local index = slot(now)
	meter.buckets[index] = (meter.buckets[index] or 0) + n
end

-- How many left during the last minute.
function RateLogic.perMinute(meter: Meter, now: number): number
	prune(meter, now)
	local total = 0
	for _, n in meter.buckets do
		total += n
	end
	return total
end

return RateLogic
