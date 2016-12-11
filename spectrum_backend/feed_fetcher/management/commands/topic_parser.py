from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from spectrum_backend.feed_fetcher.models import Topic
from spectrum_backend.feed_fetcher.models import TopicWord
from spectrum_backend.feed_fetcher.models import Tag
from ._tag_wrapper import TagWrapper

# {'Elections', 'Giuliani, Rudolph W', 'Campaign Finance', 'Clinton, Hillary Rodham', 'Cyberharassment', 'Midtown Area (Manhattan, NY)', 'Telephones and Telecommunications', 'Gingrich, Newt', 'Time Warner Inc', 'Appointments and Executive Changes', 'Mergers, Acquisitions and Divestitures', 'State Department', 'Exxon Mobil Corp', 'Christie, Christopher J', 'Patient Protection and Affordable Care Act (2010)', 'Columbia University', 'Taliban', 'Ireland', 'The Apprentice (TV Program)', 'Espionage and Intelligence Services', 'Thune, John R', 'Republican Party', 'Privacy', 'Graham, Lindsey', 'Conservation of Resources', 'WikiLeaks', 'Afghanistan War (2001-14)', 'Syria', 'McCain, John', 'Pruitt, Scott', 'Trump, Donald J', 'Presidential Election of 2016', 'Federal Budget (US)', 'Prices (Fares, Fees and Rates)', 'University of Michigan', 'Libya', 'Computer Security', 'National Security Agency', 'Television', 'Cyberattacks and Hackers', 'Fayetteville (NC)', 'Son, Masayoshi', 'Mobile Applications', 'Oil (Petroleum) and Gasoline', 'Fifth Avenue (Manhattan, NY)', 'Jones, Chuck', 'Politics and Government', 'Shutdowns (Institutional)', 'Supreme Court (US)', 'Michigan', 'Snowden, Edward J', 'Carrier Corp', 'Environmental Protection Agency', 'Layoffs and Job Reductions', 'Conway, Kellyanne', 'AT&T Inc', 'Podesta, John D', 'Burnett, Mark', 'Schumer, Charles E', 'Hate Crimes', 'Urban Areas', 'Decisions and Verdicts', 'United States', 'Energy Department', 'Trump Organization', 'Labor and Jobs', 'DiCaprio, Leonardo', 'Golf', 'Conservatism (US Politics)', 'Presidents and Presidency (US)', 'Corporate Taxes', 'Area Planning and Renewal', 'Stein, Jill', 'American Library Assn', 'Drugs (Pharmaceuticals)', 'Jones, Chuck (Union Leader)', 'Tillerson, Rex W', 'Virginia Polytechnic Institute and State University', 'Real Estate and Housing (Residential)', '3M Company', 'Customs (Tariff)', 'International Trade and World Market', 'Factories and Manufacturing', 'United States Defense and Military Forces', 'Environment', 'McConnell, Mitch', 'Translation and Interpreters', 'Surveillance of Citizens by Government', 'United States Politics and Government', 'Senate Committee on the Judiciary', 'Pence, Mike', 'Islamic State in Iraq and Syria (ISIS)', 'Collins, Susan M', 'Defense Department', 'Conflicts of Interest', 'Corporations', 'Eminent Domain', 'Mines and Mining', 'Voting and Voters', 'Minorities', 'Vandalism', 'Dimon, James', 'Louisiana', 'Boeing Company', 'Manchin, Joe III', 'WhatsApp Inc', 'Cable Television', 'Greenhouse Gas Emissions', 'Terrorism', 'Schwarzenegger, Arnold', 'Indianapolis (Ind)', 'Signal (Open Whisper Systems)', 'Global Warming', 'Federal Communications Commission', 'National Broadcasting Co', 'Energy Information Administration', 'Visas', 'National Assn of Manufacturers', 'Barrasso, John', 'Capital Punishment', 'Republican National Committee', 'Trump Tower (Manhattan, NY)', 'Carter, Ashton B', 'Libraries and Librarians', 'Senate', 'Surt (Libya)', 'Principal Financial Group Inc', 'Smith, Ronald B', 'Mattis, James N', 'Blacks', 'United Steelworkers of America', 'Air Force One (Jet)', 'Automobiles', 'Podcasts', 'Law and Legislation', 'United States Economy', 'Rosneft', 'Des Moines (Iowa)', 'Coal', 'Twitter', 'Schwarzman, Stephen A', 'Illegal Immigration', 'Health Insurance and Managed Care', 'Regulation and Deregulation of Industry', 'Colleges and Universities', 'Democratic Party', 'Afghanistan', 'Stocks and Bonds', 'Biotechnology and Bioengineering', 'Heritage Foundation', 'Amherst College', 'Ohio State University', 'Amgen Inc', 'United States International Relations', 'BlackRock Inc', 'Washington (DC)', 'Alabama', 'United States Air Force', 'Muslim Americans', 'Romney, Mitt', 'Washington Post'}

class Command(BaseCommand):
  NEW_YORK_TIMES_STRING = "New York Times"
  def handle(self, *args, **options):
    count = 0
    for tag in Tag.objects.all():
      if tag.publication_name() == self.NEW_YORK_TIMES_STRING:
        count += 1
        tag_wrapper = TagWrapper(tag.name)
        if tag_wrapper.has_tags():
          topic = Topic.objects.get_or_create(base_tag_string=tag.name)[0]
          for tag_word in tag_wrapper.words:
            try:
              TopicWord.objects.get_or_create(topic=topic, stem=tag_word.stem, pos_type=tag_word.pos_type)
            except IntegrityError:
              pass

  try:
    topic = Topic.objects.get_or_create(base_tag_string="Donald J Trump")[0]
    TopicWord.objects.get_or_create(topic=topic, stem="Donald Trump", pos_type="XX")
    TopicWord.objects.get_or_create(topic=topic, stem="Trump", pos_type="XX")
  except IntegrityError:
    pass
