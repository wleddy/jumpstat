## About Jumpstats SAC

Jumpstats is a hobby project that started because some of us were interested in finding
out what was going on with the Jump Bike bike share system in the Sacramento area.

We wanted to know how many bikes were actually available and wondered what on earth they did
with themselves all day. Where they went, how long they sat there and if they were getting enough to eat.

Fortunately for us, Jump Bikes kindly provides a way to ask their computers just these questions... well, sort of. 
What you can find out is where any available bikes are at just the moment that you ask. In order to answer our
questions we have to constantly pester Jump's computer and then we compile the information we get back into a database.

With the database we can figure out things like how many bikes actually operate in the area, how many trips they take and
even (using some guesswork, a Magic 8 Ball and a Ouija board) when they go in for recharge or service.

__DONT PANIC!__ We are not tracking you. (But Jump Bike is, just sayin') We don't know who rides a bike or where they
go on the way. We only know the starting point and the ending point of a ride.

### So without adieu being in any way furthered...

For anyone with nothing better to do (and I'm talking about you, Dan) feel free to read on for more of the details
about what we think this web site does.

#### Data source

The data is provided by Jump Bikes through their "developer API" which is 
documented [here](https://app.socialbicycles.com/developer/ "Jump Bikes Developer API").

The data we receive back is essentially a list of every bike in the area that is available for rent. This is presumably what
you see when you use the Jump Bikes app or web site. Just way less pretty.

#### Data retrieval

So that we don't become a total pain, Jump requests that we send a limited number of requests each day. We just about max out our
ration by making a request about every 9 minutes. So our data should be at worst 8 and a half minutes old.

#### What is an Available Bike

An Available Bike is simply any bike that was included in our latest data request. Again, the same as you would see on
the app.

#### How do we count Total Bikes

The Total Bikes number is any bike we have ever seen in the data. We don't know if all those bikes are still in service.
Some may have been damaged, moved to another system or who knows what. The "plan" is to periodically scan the bikes list
to find any that we haven't seen in a few weeks and remove them from our list.

#### How is a Trip identified

Pretty simple really. The first time we see a bike we make a note of it. The next time we see it in a different location
we count that as a trip.

If it's been more than 2 hours since the last time we saw the bike we assume it has been off at the Bike Spa getting
pampered and rejuvenated for another day or two of service. Heaven knows they need it. The way some people behave is just 
shameless.

#### Any thing else you'd like to know?

If you have any questions or some suggestions of some other information about the life of bikes, please feel free to 
[contact us](/contact/ "contact us").

