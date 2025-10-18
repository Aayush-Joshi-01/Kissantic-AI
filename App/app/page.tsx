import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-10">
      <header className="max-w-4xl mx-auto text-center space-y-4 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
          The Farmer&apos;s AI Friend
        </div>
        <h1 className="text-4xl md:text-5xl font-semibold text-balance">
          Kisaantic AI — Agentic agriculture for every farmer
        </h1>
        <p className="text-muted-foreground text-pretty">
          We help farmers choose the right crop, secure equipment at the best prices, and sell directly to nearby
          markets—maximizing ROI with full control.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Button asChild className="transition-transform hover:scale-[1.02]">
            <Link href="/signup">Get started</Link>
          </Button>
          <Button asChild variant="secondary" className="transition-colors hover:bg-secondary/70">
            <Link href="/chat">Open Chat</Link>
          </Button>
        </div>
      </header>

      <section className="max-w-5xl mx-auto mt-12 animate-fade-in">
        <Card>
          <CardHeader>
            <CardTitle>Our Inspiration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-pretty">
            <p>
              While my father served in the Indian administration, he witnessed dozens of farmers driven to suicide by a
              broken system that failed them. He eventually quit, but the trauma stayed with him—and with us as
              teenagers. The only thing a farmer knows in India is farming. The agony of a farmer who ends up his life
              to feed the nation has carved an impact deep in our family.
            </p>
            <p>
              I&apos;m building an Agentic AI solution to remove dependence on politics and middlemen and give farmers the
              resources, markets, and resilience they deserve.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="max-w-5xl mx-auto mt-12 grid gap-6 md:grid-cols-2 animate-slide-in-from-bottom">
        <Card>
          <CardHeader>
            <CardTitle>What it does</CardTitle>
          </CardHeader>
          <CardContent className="text-pretty space-y-3">
            <p>
              This intelligent agentic agent retrieves and fuses real-time data from government and public application databases to process information like demographics, soil erosion quality, weather, water availability for irrigation, power & energy availability, crop shortage in country etc.
            </p>
            <p>
              It determines what is the best crop to harvest at any time of the season based on historical analytics. The agent recommends and with human approval makes the rental bookings for best quality agricultural equipment like Tractors, Combines etc. for best price in the vicinity.
            </p>
            <p>
              The agent also provides the farmer with ideal ROI from the yield for the respective harvest season while recommending the best closest farmers market to sell the yield to without any middlemen. This not only gives a farmer the full value of the seed, but also gives him full control that he truly deserves avoiding the farmer crisis.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>How we built it</CardTitle>
          </CardHeader>
          <CardContent className="text-pretty space-y-3">
            <p>
              We used AWS Amplify and Next.js and built this by leveraging external API&apos;s from public and government domains for soil data, weather data, GPS Data, etc., and have added some additional information like equipment rental data, farm markets prices to our knowledge bases for inputs to our Agents from S3 and DynamoDB to process farmers requests and made recommendations.
            </p>
            <p>
              While in phase 1, the tool recommends information for farmer, in phase 2 the agents will also make the farm equipment rental bookings, reserve slots at farmers markets etc.
            </p>
            <p>
              This has been built over Amazon Bedrock leveraging Amazon Nova Lite from Amazon Marketplace.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="max-w-5xl mx-auto mt-12 grid gap-6 md:grid-cols-2 animate-slide-in-from-bottom">
        <Card>
          <CardHeader>
            <CardTitle>Challenges we ran into</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-pretty">
            <div>
              <p className="font-medium mb-1">1. Data Sourcing</p>
              <p className="text-sm text-muted-foreground">
                Biggest challenge was sourcing the data and creating knowledge bases. A lot of available data had a lot of noise and search which had to be refined. Very limited API&apos;s that were available in the market for this project.
              </p>
            </div>
            <div>
              <p className="font-medium mb-1">2. Agent Orchestration</p>
              <p className="text-sm text-muted-foreground">
                Orchestration among the Agents was a bit challenging due to the enormous amount of data that had to be processed to give farmer with the most authentic and real-time information.
              </p>
            </div>
            <div>
              <p className="font-medium mb-1">3. Model Limitations</p>
              <p className="text-sm text-muted-foreground">
                This project involves 8 Agents that uses Nova Lite. We had problems inferencing so we had to use only Nova lite or we could leverage 8 LLM&apos;s for 8 different agents for even more accurate data. This also is increasing latency in response times.
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Accomplishments that we&apos;re proud of</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-pretty">
            <div>
              <p className="font-medium mb-1">1. Complete Farming Solution</p>
              <p className="text-sm text-muted-foreground">
                Kisaan means Farmer in India. Our Agentic AI Agent helps Farmer in every step of the way, hence Kissantic AI. This tool is a one stop shop to every farmer in the world who plans to harvest their crop. This tool not only recommends the best crop to plant, but also helps farmers navigate through every stage of the harvest season from seeding to selling the yield all over the world. This tool will be every farmers best friend and avoids Farmer suicides in India and concerns all over the world.
              </p>
            </div>
            <div>
              <p className="font-medium mb-1">2. Language Translation</p>
              <p className="text-sm text-muted-foreground">
                This tool has language translation and the responses could be prompted for results to be shown in the farmers native language. Some of the languages include Hindi, French, German, Italian, etc., among other languages supported by Nova Lite.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="max-w-5xl mx-auto mt-12 grid gap-6 md:grid-cols-2 animate-fade-in">
        <Card>
          <CardHeader>
            <CardTitle>What we learned</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-pretty">
            <div>
              <p className="font-medium mb-1">1. Power of Single Ecosystem</p>
              <p className="text-sm text-muted-foreground">
                Being in single ecosystem like Amazon has helped us build this entire tool in less than 30 days from concept to productionizing this.
              </p>
            </div>
            <div>
              <p className="font-medium mb-1">2. Bedrock Flexibility</p>
              <p className="text-sm text-muted-foreground">
                Using Bedrock has provided so much flexibility to build everything under one single ecosystem and reduce complexities that are caused by hybrid ecosystems. Amazon has become one stop shop for all our AI needs.
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>What&apos;s next for Kisaantic AI</CardTitle>
          </CardHeader>
          <CardContent className="text-pretty">
            <p>
              Create additional agents that will not only recommend best prices and places to procure fertilizers, seeds, farm equipment rentals, farming machinery drivers, slots at farm markets etc., but will also make the reservations automatically on behalf of farmers making it a complete automatic farming experience for customers resulting in maximum ROI.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
