#!/usr/bin/env python
from . import errors as exceptions
import nomenclate.settings as settings


class TokenMatch(object):

    def __init__(self, regex_match, substitution, group_name='token'):
        self.match = regex_match.group(group_name)
        self.start = regex_match.start(group_name)
        self.end = regex_match.end(group_name)
        self.sub = str(substitution)

    @property
    def span(self):
        return self.end - self.start

    def adjust_position(self, other, adjust_by_sub_delta=True):
        self._validate_adjuster(other)
        adjustment = other.span - len(other.sub) if adjust_by_sub_delta else other.span
        if adjustment:
            self._adjust_order(adjustment)

    def _validate_adjuster(self, other):
        if not isinstance(other, self.__class__):
            raise IOError('Only TokenMatch objects are valid inputs to adjust_position')

        other.overlaps(self)

        if self < other:
            raise IndexError('Current TokenMatch is not affected by input TokenMatch\n\t%s\n\t%s' % (repr(self),
                                                                                                     repr(other)))

    def _adjust_order(self, adjust_value):
        self.start -= adjust_value
        self.end -= adjust_value

    def overlaps(self, other):
        if self in other or other in self:
            raise exceptions.OverlapError('Match %s overlaps with an existing match:\n\t%s\n\t%s' % (self.match,
                                                                                                     self, other))
        return True

    def __contains__(self, other):
        try:
            return self.start < other.start < self.end or self.start < other.end < self.end
        except:
            raise NotImplementedError(
                '<%s>.__contains__ does not handle <%s>' % (self.__class__.__name__, type(other)))

    def __eq__(self, other):
        try:
            return (self.start == other.start and self.end == other.end and
                    self.match == other.match and self.sub == other.sub)
        except:
            raise NotImplementedError(
                '<%s>.__eq__ does not handle <%s>' % (self.__class__.__name__, type(other)))

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.end <= other.start
        else:
            raise NotImplementedError

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.start >= other.end
        else:
            raise NotImplementedError

    def __repr__(self):
        return '<%s %s (%d)- [%d:%d] - replacement = %s>' % (self.__class__.__name__,
                                                             self.match, self.span, self.start, self.end, self.sub)

    def __str__(self):
        return '%s:%s' % (self.match, self.sub)


class Nomenclative(object):

    def __init__(self, input_str):
        self.raw_formatted_string = input_str
        self.token_matches = []

    def process_matches(self):
        build_str = self.raw_formatted_string
        for token_match in self.token_matches:
            # Do not process static token matches
            if token_match.match.startswith('(') or token_match.match.endswith(')'):
                continue

            if token_match.match == build_str[token_match.start:token_match.end]:
                build_str = build_str[:token_match.start] + token_match.sub + build_str[token_match.end:]
                self.adjust_other_matches(token_match)
        return build_str

    def adjust_other_matches(self, adjuster_match):
        for token_match in [token_match for token_match in self.token_matches if token_match != adjuster_match]:
            try:
                token_match.adjust_position(adjuster_match)
            except IndexError:
                pass
        adjuster_match.end = adjuster_match.start + len(adjuster_match.sub)
        adjuster_match.match = adjuster_match.sub

    def add_match(self, regex_match, substitution):
        token_match = TokenMatch(regex_match, substitution)
        try:
            self.validate_match(token_match)
            self.token_matches.append(token_match)
        except (IndexError, exceptions.OverlapError):
            raise exceptions.OverlapError('Not adding match %s as it conflicts with a preexisting match' % token_match)

    def validate_match(self, token_match_candidate):
        for token_match in self.token_matches:
            try:
                token_match.overlaps(token_match_candidate)
            except exceptions.OverlapError:
                raise exceptions.OverlapError(
                    "Cannot add match %s due to overlap with %s" % (token_match, token_match_candidate))

    def __str__(self):
        matches = ' ' if not self.token_matches else ' '.join(map(str, self.token_matches))
        return 'format: %s: %s' % (self.raw_formatted_string, matches)
