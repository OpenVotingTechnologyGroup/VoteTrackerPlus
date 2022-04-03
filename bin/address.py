#  VoteTrackerPlus
#   Copyright (C) 2022 Sandy Currier
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""An Address class for VoteTracker+"""

import re
import posixpath
from common import Globals

class Address:
    """A class to create an address object, which is just an address
    in a conanical dictionary form.  This just holds the address and
    will not validate it against a config and addpress_map data.  The
    class supports return the Address as either a string or a
    dictionary.

    Implementation note - individual address fields are never set to
    NoneType - if empty/blank, they are set to the empty string "".
    And all fields are strings, not numbers.
    """

    # Legitimate keys in the correct order
    _keys = ['number', 'street', 'substreet', 'town', 'state',
                 'country', 'zipcode']
    # Map the ElectionConfig 'kind' to the Address 'kind'
    _kinds_map = {'state':'states', 'town':'towns', 'county':'counties',
                      'SchoolDistrict':'SchoolDistricts',
                      'CouncilDistrict':'CouncilDistricts',
                      'Precinct':'Precincts'}

    @staticmethod
    def convert_address_to_num_street(address):
        """Convert a street address string to number and street"""
        return re.split(r'\s+', address, 1)

    @staticmethod
    def create_address_from_args(args, args_to_strip):
        """Helper function to strip just the address specific switches
        from the program args and return the new address.
        """
        my_args = dict(vars(args))
        for key in args_to_strip:
            del my_args[key]
        # if address was supplied, get rid of that too
        if my_args['address']:
            my_args['number'], my_args['street'] = \
            Address.convert_address_to_num_street(my_args['address'])
        del my_args['address']
        return Address(**my_args)

    @staticmethod
    def add_address_args(parser, blank=True):
        """Helper function to add standard address program switches to argparse"""
#        parser.add_argument('-c', "--csv",
#                                help="a comma separated address")
#        parser.add_argument('-r', "--street",
#                                help="the street/road field of an address, \
#                                in which case the address is the number")
#        parser.add_argument('-z', "--zipcode",
#                                help="the zipcode field of an address")
        if blank:
            parser.add_argument('-a', "--address",
                                    help="the number and name of the \
                                    street address (space separated)")
            parser.add_argument('-b', "--substreet",
                                    help="the substreet field of an address")
        parser.add_argument('-t', "--town",
                                help="the town field of an address")
        parser.add_argument('-s', "--state",
                                help="the state/province field of an address")

    # pylint: disable=too-many-arguments
    def __init__(self, number="", street="", substreet="", town="",
                     state="", country="", zipcode="", csv="",
                     voting_center=False):
        """At the moment support only support a csv keyword and a
        reasonable dictionary set of keywords.
        """
        self.address = {}
        self.address['number'] = number
        self.address['street'] = street
        self.address['substreet'] = substreet
        self.address['town'] = town
        self.address['state'] = state
        self.address['country'] = country
        self.address['zipcode'] = zipcode
        # the ordered list of active GGOs for this address
        self.active_ggos = []
        # the location of the address's blank ballot and CVRs folder.
        # Note - this currently is the last active_ggos entry but that
        # is due to the implemention, which probably needs to change
        # at some point.
        self.ballot_node = ""
        self.ballot_subdir = ""

        if csv: # pylint: disable=consider-iterating-dictionary
            address_fields = [x.strip() for x in re.split(r'\s*,\s*', csv)]
            self.address['number'] = address_fields[0]
            self.address['street'] = address_fields[1]
            if address_fields == 5:
                self.address['substreet'] = address_fields[2]
                self.address['town'] = address_fields[3]
                self.address['state'] = address_fields[4]
            else:
                self.address['substreet'] = ""
                self.address['town'] = address_fields[2]
                self.address['state'] = address_fields[3]

        # Note - an address needs all 'required' address fields to be specified
        required_fields = Globals.get('REQUIRED_GGO_ADDRESS_FIELDS').copy()
        if not voting_center:
#            import pdb; pdb.set_trace()
            required_fields += Globals.get('REQUIRED_NG_ADDRESS_FIELDS')
        missing_keys = [key for key in required_fields
                            if not Address.get(self, key)]
        if missing_keys:
            raise NameError(("Addresses must include values for the following fields: "
                                 f"{required_fields}"
                                 "The following fields are undefined: "
                                 f"{missing_keys}"))

    def __iter__(self):
        """Return an iterator for the address attribute"""
        return iter(self.address)

    def __str__(self):
        """Return a space separated string of the address"""
        nice_string = ""
        for key in Address._keys:
            if self.address[key]:
                nice_string += " " + self.address[key]
        return nice_string.strip()

    def get(self, name):
        """A generic getter - will raise a NameError if name is not defined"""
        if name in Address._keys:
            return self.address[name]
        if name == 'str_address':
            # return the number and street - ZZZ ignore substreet for now
            nice_string = self.address['number'] + ' ' + self.address['street']
            return nice_string.strip()
        if name == 'active_ggos':
            return self.active_ggos
        if name == 'ballot_node':
            return self.ballot_node
        if name == 'ballot_subdir':
            return self.ballot_subdir
        raise NameError(f"Name {name} not accepted/defined for set()")

    def set(self, name, value):
        """A generic setter - will raise a NameError if name is not defined """
        if name in Address._keys:
            value = "" if value is None else value
            self.address[name] = value
        else:
            raise NameError(f"Name {name} not accepted/defined for Address.set()")

    def dict(self):
        """Return a dictionary of the address"""
        address = {}
        for key in Address._keys:
            address[key] = self.address[key]
        return address

    def match(self, regex):
        """Will regex the supplied regex against the address"""
        # For now if regex is a string, it is a number and street
        # address only
        if isinstance(regex, str):
            return re.match(regex, self.address['number'] + ' ' + self.address['street'])
        raise ValueError((f"Unsupoorted Address match regex ({regex}) - ",
                        "supply more quality pizza"))

    def map_ggos(self, config):
        """Will map an address onto the ElectionConfig data
        """
        footsteps = set()
        addr_hits = []

        def walk_descendants(node_of_interest):
            """Will find all descendantss of this node"""
            # pylint: disable=too-many-nested-blocks
            if 'unique-ballots' in config.node(node_of_interest)['address_map']:
                for entry in config.node(node_of_interest)['address_map']['unique-ballots']:
                    for addr in entry['addresses']:
#                        import pdb; pdb.set_trace()
                        if self.match(addr):
                            # add the ggos in order if not already present
                            for ggo in entry['ggos']:
                                if ggo not in self.active_ggos:
                                    self.active_ggos.append(ggo)
                            addr_hits.append(node_of_interest)
            footsteps.add(node_of_interest)
            for child in config.descendants(node_of_interest):
                if child in footsteps:
                    continue
                walk_descendants(child)

        # Note - the root GGO always contributes
        self.active_ggos.append('.')
        breadcrumbtrail = ''
        # Walk the address in DAG order from root to the prescribed leafs
        for field in Globals.get('REQUIRED_GGO_ADDRESS_FIELDS'):
            # For this field in the address, get the correct ggo kind and instance
            node = posixpath.join(breadcrumbtrail, 'GGOs',
                                      Address._kinds_map[field], self.get(field))
            # Better to sanity check now later
            if not config.is_node(node):
                raise ValueError(f"Bad ElectionConfig node name ({node})")
            self.active_ggos.append(node)
            breadcrumbtrail = node

        # The above for loop will append in order the explicit
        # REQUIRED_GGO_ADDRESS_FIELDS ggo ordering.  Once in the leaf
        # node, just match against the N possible unique-ballots
        # entries.  Walk all entries regardless of the number of hits
        # and raise an error if multiple or no hits.
        the_leaf_node = self.active_ggos[-1]
        # Look for address hits
        walk_descendants(the_leaf_node)
        # test to see how many address hits were found
        if len(addr_hits) == 0:
            raise ValueError(f"The supplied address ({self}) "
                                 "does not match any address_map")
        if len(addr_hits) > 1:
            raise ValueError(f"The supplied address ({self}) "
                                 "matches multiple address_map files: "
                                 f"{addr_hits}")
        # Note1: the subdir should already have the correct
        # os.path.sep.  Note2: The ballot_subdir could in theory be
        # the GGO that defines the matching address regex OR simply be
        # the_leaf_node.  For now just use the the_leaf_node
        self.ballot_subdir = config.get_node(the_leaf_node, 'subdir')
#        self.ballot_subdir = config.get_node(addr_hits[0], 'subdir')
        # Ditto for ballot_node - set the blank-ballot / CVRs node
        self.ballot_node = the_leaf_node
#        self.ballot_node = addr_hits[0]

# EOF
