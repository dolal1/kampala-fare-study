# Experiment proposals (drafts)

Written before the data. Each one names the result from `out/summary.md` that would
justify running it; if the data does not show that, drop or rewrite the proposal.

The proposals are written as if for SafeBoda, to keep them concrete. The same designs apply
to any of the apps. This is independent work, not commissioned by or affiliated with any of them.

Changing a fare for some passengers also changes which trips drivers accept, so drivers
and passengers in a simple user-level A/B test interfere with each other. Each design
below therefore switches a whole area on and off over time (a switchback test) and
compares treated hours with control hours in the same area.

## 1. Off-peak fare cut on routes where SafeBoda is priced above rivals

- **Run it if:** SafeBoda's median fare is clearly above the cheapest rival on some
  routes at midday.
- **Hypothesis:** matching the cheapest rival at midday on those corridors raises
  completed trips by more than it lowers revenue per trip.
- **Primary metric:** completed trips per hour in the corridor.
- **Guardrails:** driver earnings per online hour; pickup ETA; gross revenue.
- **Design:** switchback by corridor, alternating treatment and control in blocks of a
  few hours, for at least two weeks so every weekday and hour appears in both arms.
- **Decision rule:** ship if trips rise and driver earnings per hour do not fall.

## 2. Driver incentive at the times ETAs are longest

- **Run it if:** SafeBoda's pickup ETA is longer than rivals' in one time band.
- **Hypothesis:** a per-trip bonus in that band brings more drivers online and shortens
  ETA enough to lift the share of requests that become trips.
- **Primary metric:** request-to-trip completion rate.
- **Guardrails:** incentive cost per extra completed trip; ETA in the hours just after
  the bonus ends, in case supply is only shifted.
- **Design:** switchback by zone and day for the target band.
- **Decision rule:** ship if the cost per extra trip is below the margin on that trip.

## 3. Scheduled Trips prompt for regular morning commuters

- **Run it if:** morning-peak fares or ETAs are the most variable of any band.
- **Hypothesis:** offering a fixed-fare scheduled trip to passengers who ride the same
  route on several mornings a week raises their weekly trips and retention.
- **Primary metric:** trips per passenger per week over four weeks.
- **Guardrails:** scheduled-trip cancellation and no-show rate; driver acceptance rate.
- **Design:** passenger-level randomised prompt. Supply effects are small because the
  prompt targets a small share of morning demand; check that assumption in the data.
- **Decision rule:** ship if weekly trips rise and no-shows stay under an agreed limit.
