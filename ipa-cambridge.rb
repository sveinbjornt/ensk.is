#!/usr/bin/env ruby1.8

# Query Cambridge online dictionary for IPA pronunciation of English words.
#
# A tad slow and messy, but works (as of 2010-11-29).

require 'rubygems'
require 'nokogiri'
require 'open-uri'

BASE_URI='http://dictionary.cambridge.org'
SEARCH_URI='http://dictionary.cambridge.org/search/english/?q=%s'
EXACT_URI='http://dictionary.cambridge.org/dictionary/english/%s'

def get_pron(exact_uri)
  page = Nokogiri::HTML(open(exact_uri))
  # TODO: tag US prons
  pron_els = page.css('*.pron')
  return pron_els.collect do |pron|
    pron.content
  end
end

def query_word(word)
  begin
    return get_pron(format(EXACT_URI, word))
  rescue OpenURI::HTTPError => error
    if error.io.status[0] != '404'
      raise error

    else
      search = format(SEARCH_URI, word)
      respage = Nokogiri::HTML(open(search))
      results = respage.css('ul.result-list > li')
      res_uris = []
      results.each do |res|
        res_text = res.css('span.BASE').first.content
        if res_text.strip.downcase == word.downcase
          res_uris << res.css('a').first['href']
        end
      end

      the_prons = []
      res_uris.each do |uri|
        # TODO: be robust for the eventuality of non-relative hrefs
        prons = get_pron(BASE_URI + uri)
        unless the_prons.include? prons
          the_prons << prons
        end
      end
      return the_prons
    end
  end
end

begin
  puts query_word(ARGV[0])
rescue OpenURI::HTTPError => ex
  puts "HTTP error: " + ex
  exit 1
end

# uri = format(DICT_URI, word)

# results = []

# begin
#   doc = Nokogiri::HTML(open(uri))
# rescue OpenURI::HTTPError

# the_prons = doc.css('span.pron')
# the_prons.each do |pron|
#   puts pron.content
# end
