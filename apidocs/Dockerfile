FROM ruby:2.3
FROM silverlogic/apidocs-dev

# throw errors if Gemfile has been modified since Gemfile.lock
RUN bundle config --global frozen 1

WORKDIR /usr/src/app

COPY Gemfile Gemfile.lock ./
RUN bundle install

CMD ["middleman", "server"]
