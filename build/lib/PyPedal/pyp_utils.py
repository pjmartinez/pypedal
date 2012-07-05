#!/usr/bin/python

###############################################################################
# NAME: pyp_utils.py
# VERSION: 2.0.0 (29SEPTEMBER2010)
# AUTHOR: John B. Cole, PhD (john.cole@ars.usda.gov)
# LICENSE: LGPL
###############################################################################
# FUNCTIONS:
#   load_pedigree()
#   preprocess()
#   new_preprocess()
#   set_ancestor_flag()
#   set_generation()
#   set_age()
#   set_species()
#   assign_sexes()
#   assign_offspring()
#   assign_upg()
#   reorder()
#   fast_reorder()
#   renumber()
#   load_id_map()
#   delete_id_map()
#   id_map_new_to_old()
#   trim_pedigree_to_year()
#   pedigree_range()
#   sort_dict_by_keys()
#   sort_dict_by_values()
#   simple_histogram_dictionary()
#   reverse_string()
#   pyp_nice_time()
#   string_to_table_name()
#   pyp_datestamp()
#   subpedigree()
#   founders_from_list()
#   founder_allele_dict()
###############################################################################

## @package pyp_utils
# pyp_utils contains a set of procedures for creating and operating on PyPedal pedigrees.
# This includes routines for reordering and renumbering pedigrees, as well as for modifying
# pedigrees.

import copy, logging, numpy, os, string, sys, time
import pyp_demog
import pyp_metrics
import pyp_newclasses

##
# set_ancestor_flag() loops through a pedigree to build a dictionary of all of the parents
# in the pedigree.  It then sets the ancestor flags for the parents.  set_ancestor_flag()
# expects a reordered and renumbered pedigree as input!
# @param pedobj A PyPedal NewPedigree object.
# @retval 0 for failure and 1 for success.
def set_ancestor_flag(pedobj):
    """
    set_ancestor_flag() loops through a pedigree to build a dictionary of all of the
    parents in the pedigree.  It then sets the ancestor flags for the parents.
    set_ancestor_flag() expects a reordered and renumbered pedigree as input!
    """
    try:
        parents = {}        # holds a list of animals who are parents
        l = len(pedobj.pedigree)
        if l < 2:
            print '[ERROR]: pedobj.pedigree only contains one record -- nothing to do in set_ancestor_flag()!'
            return

        pedobj.pedigree.reverse()     # We want to go from young to old.
        for i in xrange(l):
            # Put the animalIDs of the animals parents in the parents list if
            # they are known and are not already in the dictionary.
            if pedobj.kw['messages'] == 'debug':
                print '[DEBUG]:\t\tanimal: %s\tsire: %s\tdam: %s' % (pedobj.pedigree[i].animalID,pedobj.pedigree[i].sireID,pedobj.pedigree[i].damID)
            #if int(pedobj.pedigree[i].sireID) != 0:
            if pedobj.pedigree[i].sireID != pedobj.kw['missing_parent']:
                try:
                    _i = parents[int(pedobj.pedigree[i].sireID)]
                except:
                    parents[int(pedobj.pedigree[i].sireID)] = int(pedobj.pedigree[i].sireID)
                    pedobj.pedigree[int(pedobj.pedigree[i].sireID)-1].ancestor = 1

            #if int(pedobj.pedigree[i].damID) != 0:
            if pedobj.pedigree[i].damID != pedobj.kw['missing_parent']:
                try:
                    _i = parents[int(pedobj.pedigree[i].damID)]
                except:
                    parents[int(pedobj.pedigree[i].damID)] = int(pedobj.pedigree[i].damID)
                    pedobj.pedigree[int(pedobj.pedigree[i].damID)-1].ancestor = 1
        pedobj.pedigree.reverse()     # Put pedobj.pedigree back the way it was -- pass-by-reference, don't you know!

        if pedobj.kw['file_io']:
            try:
                a_outputfile = '%s%s%s' % (pedobj.kw['filetag'],'_ancestors','.dat')
                aout = open(a_outputfile,'w')
                aout.write('# FILE: %s\n' % a_outputfile)
                aout.write('# ANCESTOR list produced by PyPedal.\n')
                for l in parents.keys():
                    aout.write('%s\n' % l)
                aout.close()
                logging.info('pyp_utils/set_ancestor_flag() wrote file %s.' % (a_outputfile))
            except:
                logging.error('pyp_utils/set_ancestor_flag() could not write file %s.' % (a_outputfile))

        return 1

    except:
        a_outputfile = '%s%s%s' % (pedobj.kw['filetag'],'_ancestors','.dat')
        logging.error('pyp_utils/set_ancestor_flag() could not write file %s.' % (a_outputfile))
        return 0

##
# set_generation() Works through a pedigree to infer the generation to which an animal
# belongs based on founders belonging to generation 1.  The igen assigned to an animal
# as the larger of sire.igen+1 and dam.igen+1.  This routine assumes that myped is
# reordered and renumbered.
# @param pedobj A PyPedal NewPedigree object.
# @retval 0 for failure and 1 for success.
def set_generation(pedobj):
    """
    set_generation() Works through a pedigree to infer the generation to which an animal
    belongs based on founders belonging to generation 1.  The igen assigned to an animal
    as the larger of sire.igen+1 and dam.igen+1.  This routine assumes that myped is
    reordered and renumbered.
    """
    try:
        if pedobj.kw['messages'] == 'debug':
            print '[NOTE]: pyp_utils/set_generation() assigning inferred generations in pedigree %s.' % (pedobj.kw['pedname'])
        for i in range(pedobj.metadata.num_records):
            #if int(pedobj.pedigree[i].sireID) == 0 and int(pedobj.pedigree[i].damID) == 0:
            if pedobj.pedigree[i].sireID == pedobj.kw['missing_parent'] and  pedobj.pedigree[i].damID == pedobj.kw['missing_parent']:
                if pedobj.kw['gen_coeff']:
                    pedobj.pedigree[i].gencoeff = 1.
                    pedobj.pedigree[i].igen = int(round(pedobj.pedigree[i].gencoeff))
                else:
                    pedobj.pedigree[i].igen = 1
            #elif int(pedobj.pedigree[i].sireID) == 0:
            elif pedobj.pedigree[i].sireID == pedobj.kw['missing_parent']:
                if pedobj.kw['gen_coeff']:
                    pedobj.pedigree[i].gencoeff = ( pedobj.pedigree[int(pedobj.pedigree[i].damID)-1].gencoeff / 2. ) + 1.
                    pedobj.pedigree[i].igen = int(round(pedobj.pedigree[i].gencoeff))
                else:
                    pedobj.pedigree[i].igen = pedobj.pedigree[int(pedobj.pedigree[i].damID)-1].igen + 1
            #elif int(pedobj.pedigree[i].damID) == 0:
            elif pedobj.pedigree[i].damID == pedobj.kw['missing_parent']:
                if pedobj.kw['gen_coeff']:
                    pedobj.pedigree[i].gencoeff = ( pedobj.pedigree[int(pedobj.pedigree[i].sireID)-1].gencoeff / 2. ) + 1.
                    pedobj.pedigree[i].igen = int(round(pedobj.pedigree[i].gencoeff))
                else:
                    pedobj.pedigree[i].igen = pedobj.pedigree[int(pedobj.pedigree[i].sireID)-1].igen + 1
            else:
                if pedobj.kw['gen_coeff']:
                    pedobj.pedigree[i].gencoeff = ( pedobj.pedigree[int(pedobj.pedigree[i].damID)-1].gencoeff + pedobj.pedigree[int(pedobj.pedigree[i].sireID)-1].gencoeff / 2. ) + 1.
                    pedobj.pedigree[i].igen = int(round(pedobj.pedigree[i].gencoeff))
                else:
                    pedobj.pedigree[i].igen = max(pedobj.pedigree[int(pedobj.pedigree[i].sireID)-1].igen + 1,pedobj.pedigree[int(pedobj.pedigree[i].damID)-1].igen + 1)
        logging.info('pyp_utils/set_generation() assigned inferred generations in pedigree %s' % (pedobj.kw['pedname']))
        return 1
    except:
        logging.error('pyp_utils/set_generation() was unable to assign inferred generations in pedigree %s' % (pedobj.kw['pedname']))
        return 0

##
# set_age() Computes ages for all animals in a pedigree based on the global
# BASE_DEMOGRAPHIC_YEAR defined in pyp_demog.py.  If the by is unknown, the
# inferred generation is used.  If the inferred generation is unknown, the
# age is set to -999.
# @param pedobj A PyPedal pedigree object.
# @retval 0 for failure and 1 for success.
def set_age(pedobj):
    """
    set_age() Computes ages for all animals in a pedigree based on the global
    BASE_DEMOGRAPHIC_YEAR defined in pyp_demog.py.  If the by is unknown, the
    inferred generation is used.  If the inferred generation is unknown, the
    age is set to -999.
    """
    try:
        if pedobj.kw['messages'] == 'debug':
            print '[NOTE]: pyp_utils/set_age() assigning inferred ages in pedigree %s.' % (pedobj.kw['pedname'])
        l = len(pedobj.pedigree)
        for i in range(l):
            if pedobj.pedigree[i].by == -999 and pedobj.pedigree[i].igen == -999:
                pedobj.pedigree[i].age = -999
            elif pedobj.pedigree[i].by == -999 and pedobj.pedigree[i].igen != -999:
                pedobj.pedigree[i].age = pedobj.pedigree[i].igen
            else:
                pedobj.pedigree[i].age = pedobj.pedigree[i].by - pyp_demog.BASE_DEMOGRAPHIC_YEAR
        logging.info('pyp_utils/set_age() assigned ages in pedigree %s' % (pedobj.kw['pedname']))
        return 1
    except:
        logging.error('pyp_utils/set_age() was unable to assign ages in pedigree %s' % (pedobj.kw['pedname']))
        return 0

##
# set_species() assigns a specie to every animal in the pedigree.
# @param pedobj A PyPedal pedigree object.
# @param species A PyPedal string.
# @retval 0 for failure and 1 for success.
def set_species(pedobj, species='u'):
    """
    set_species() assigns a specie to every animal in the pedigree.
    """
    try:
        if pedobj.kw['messages'] == 'debug':
            print '[NOTE]: pyp_utils/set_species() assigning specie %s to all animals in pedigree %s.' % (species, pedobj.kw['pedname'])
        l = len(pedobj.pedigree)
        for i in range(l):
            if len(species) > 0:
                pedobj.pedigree[i].species = species
            else:
                pedobj.pedigree[i].species = 'u'
        logging.info('pyp_utils/set_species() assigned a specie in pedigree %s' % (pedobj.kw['pedname']))
        return 1
    except:
        logging.error('pyp_utils/set_age() was unable to assign ages in pedigree %s' % (pedobj.kw['pedname']))
        return 0

##
# assign_sexes() assigns a sex to every animal in the pedigree using sire and daughter lists for improved accuracy.
# @param pedobj A renumbered and reordered PyPedal pedigree object.
# @retval 0 for failure and 1 for success.
def assign_sexes(pedobj):
    """
    assign_sexes() assigns a sex to every animal in the pedigree using sire and daughter
    lists for improved accuracy.
    """
    try:
        if pedobj.kw['messages'] == 'verbose':
            print '[NOTE]: pyp_utils/assign_sexes() assigning a sex to all animals in pedigree %s.' % (pedobj.kw['pedname'])
        for _m in pedobj.pedigree:
            if _m.sireID == pedobj.kw['missing_parent'] and  _m.damID == pedobj.kw['missing_parent']:
                pass
            elif _m.sireID == pedobj.kw['missing_parent']:
                if pedobj.pedigree[int(_m.damID)-1].sex != 'f':
                    if pedobj.kw['debug_messages']:
                        print '\t\tAnimal %s sex changed from\t%s\tto\tf' % (_m.damID,pedobj.pedigree[int(_m.damID)-1].sex)
                    pedobj.pedigree[int(_m.damID)-1].sex = 'f'
            elif _m.damID == pedobj.kw['missing_parent']:
                if pedobj.pedigree[int(_m.sireID)-1].sex != 'm':
                    if pedobj.kw['debug_messages']:
                        print '\t\tAnimal %s sex changed from\t%s\tto\tm' % (_m.sireID,pedobj.pedigree[int(_m.sireID)-1].sex)
                    pedobj.pedigree[int(_m.sireID)-1].sex = 'm'
            else:
                if pedobj.pedigree[int(_m.damID)-1].sex != 'f':
                    if pedobj.kw['debug_messages']:
                        print '\t\tAnimal %s sex changed from\t%s\tto\tf' % (_m.damID,pedobj.pedigree[int(_m.damID)-1].sex)
                    pedobj.pedigree[int(_m.damID)-1].sex = 'f'
                if pedobj.pedigree[int(_m.sireID)-1].sex != 'm':
                    if pedobj.kw['debug_messages']:
                        print '\t\tAnimal %s sex changed from\t%s\tto\tm' % (_m.sireID,pedobj.pedigree[int(_m.sireID)-1].sex)
                    pedobj.pedigree[int(_m.sireID)-1].sex = 'm'
        logging.info('pyp_utils/assign_sexes() assigned sexes in pedigree %s' % (pedobj.kw['pedname']))
        return 1
    except:
        logging.error('pyp_utils/assign_sexes() was unable to assign sexes in pedigree %s' % (pedobj.kw['pedname']))
        return 0

##
# assign_offspring() assigns offspring to their parent(s)'s unknown sex offspring list (well, dictionary).
# @param pedobj An instance of a NewPedigree object.
# @retval 0 for failure and 1 for success.
def assign_offspring(pedobj):
    """
    assign_offspring() assigns offspring to their parent(s)'s unknown sex offspring list
    (well, dictionary).
    """
    try:
        if pedobj.kw['messages'] == 'debug':
            print '[NOTE]: pyp_utils/assign_offspring() assigning offspring to all parents in pedigree %s.' % (species, pedobj.kw['pedname'])
        for _m in pedobj.pedigree:
            pedobj.pedigree[int(_m.animalID)-1].sons = {}
            pedobj.pedigree[int(_m.animalID)-1].daus = {}
            pedobj.pedigree[int(_m.animalID)-1].unks = {}
        if 'x' not in pedobj.kw['pedformat']:
            for _m in pedobj.pedigree:
                if _m.sireID == pedobj.kw['missing_parent'] and _m.damID == pedobj.kw['missing_parent']:
                    pass
                elif _m.sireID == pedobj.kw['missing_parent']:
                    pedobj.pedigree[int(_m.damID)-1].unks[_m.animalID] = _m.animalID
                elif _m.damID == pedobj.kw['missing_parent']:
                    pedobj.pedigree[int(_m.sireID)-1].unks[_m.animalID] = _m.animalID
                else:
                    pedobj.pedigree[int(_m.damID)-1].unks[_m.animalID] = _m.animalID
                    pedobj.pedigree[int(_m.sireID)-1].unks[_m.animalID] = _m.animalID
        else:
            # We purportedly know animal sexes, so put the offspring in the correct
            # lists.
            for _m in pedobj.pedigree:
                if _m.sex == 'm' or _m.sex == 'M':
                    if _m.sireID != pedobj.kw['missing_parent']:
                        #print 'Sire %s has son %s' % (_m.sireID, _m.animalID)
                        pedobj.pedigree[int(_m.sireID)-1].sons[_m.animalID] = _m.animalID
                    if _m.damID != pedobj.kw['missing_parent']:
                        #print 'Dam %s has son %s' % (_m.damID, _m.animalID)
                        pedobj.pedigree[int(_m.damID)-1].sons[_m.animalID] = _m.animalID
                elif _m.sex == 'f' or _m.sex == 'F':
                    if _m.sireID != pedobj.kw['missing_parent']:
                        #print 'Sire %s has daughter %s' % (_m.sireID, _m.animalID)
                        pedobj.pedigree[int(_m.sireID)-1].daus[_m.animalID] = _m.animalID
                    if _m.damID != pedobj.kw['missing_parent']:
                        #print 'Dam %s has daughter %s' % (_m.sireID, _m.animalID)
                        pedobj.pedigree[int(_m.damID)-1].daus[_m.animalID] = _m.animalID
                else:
                    if _m.sireID != pedobj.kw['missing_parent']:
                        #print 'Sire %s has unknown %s' % (_m.sireID, _m.animalID)
                        pedobj.pedigree[int(_m.sireID)-1].unks[_m.animalID] = _m.animalID
                    if _m.damID != pedobj.kw['missing_parent']:
                        #print 'Dam %s has unknown %s' % (_m.sireID, _m.animalID)
                        pedobj.pedigree[int(_m.damID)-1].unks[_m.animalID] = _m.animalID
        logging.info('pyp_utils/assign_offspring() assigned offspring in pedigree %s' % (pedobj.kw['pedname']))
        return 1
    except:
        logging.error('pyp_utils/assign_offspring() was unable to assign offspring in pedigree %s' % (pedobj.kw['pedname']))
        return 0

##
# assign_upg() assigns pseudo-parents to animals with unknown (missing) parents. The
# pseudo-parents can bbe used as Westell groups in an animal model.
# @param pedobj An instance of a PyPedal NewPedigree object.
# @retval None
def assign_upg(pedobj):
    """
    assign_upg() assigns pseudo-parents to animals with unknown (missing) parents. The
    pseudo-parents can bbe used as Westell groups in an animal model.
    """
    for p in pedobj:
        if pedobk.kw['pedformat'] == 'asd' or  pedobk.kw['pedformat'] == 'ASD':
	    p.sireID = -999999
	    p.sireName = 'Sire_UPG'
	else:
            pass

##
# reorder() renumbers a pedigree such that parents precede their offspring in the
# pedigree.  In order to minimize overhead as much as is reasonably possible,
# a list of animal IDs that have already been seen is kept.  Whenever a parent
# that is not in the seen list is encountered, the offspring of that parent is
# moved to the end of the pedigree.  This should ensure that the pedigree is
# properly sorted such that all parents precede their offspring.  myped is
# reordered in place.  reorder() is VERY slow, but I am pretty sure that it works
# correctly.
# @note Deprecated
# @param myped A PyPedal pedigree object.
# @param filetag A descriptor prepended to output file names.
# @param io Indicates whether or not to write the reordered pedigree to a file (yes|no).
# @param missingparent Indicates the value used to indicate a missing parent.
# @param debug Toggles debugging messages on and off.
# @param max_rounds Maximum times to iterate through a pedigree trying to reorder it.
# @retval A reordered PyPedal pedigree.
def reorder(myped, filetag='_reordered_', io='no', missingparent=0, debug=0, max_rounds=100):
    """
    Renumber a pedigree such that parents precede their offspring in the
    pedigree.  In order to minimize overhead as much as is reasonably possible,
    a list of animal IDs that have already been seen is kept.  Whenever a parent
    that is not in the seen list is encountered, the offspring of that parent is
    moved to the end of the pedigree.  This should ensure that the pedigree is
    properly sorted such that all parents precede their offspring.  myped is
    reordered in place.

    reorder() is VERY slow, but I am pretty sure that it works correctly.
    """
    l = len(myped)
    _passnum = 1     # we are going to count how many passes through the
                     # pedigree are needed to sort it.
    _moved_counter = 0
    _last_founder = 0

    # These are "Avoiding dots..." optimizations to eliminate/reduce
    # function reevaluation as described in the PythonSpeed/PerformanceTips
    # wiki at:
    # http://wiki.python.org/moin/PythonSpeed/PerformanceTips
    mypedins = myped.insert
    mypedidx = myped.index
    copycopy = copy.copy

    # Move all founders to the start of the pedigree
    founderlist = []
    for i in xrange(l):
        if myped[i].sireID == missingparent and myped[i].damID == missingparent:
            founderlist.append(i)
    # Founderlist stores the indices of founders. We go from left-to-right
    # to preserve the indices of founders at the end of the pedigree.
    founderlist.sort()
    #print 'founderlist: ', founderlist
    for f in founderlist:
        # Make a copy of the founder
        _founder = copycopy(myped[f])
        # Delete the original the original founder record
        del myped[f]
        # Prepend the copy of the founder record to the pedigree
        mypedins(0, _founder)

    # order is a list that is used to keep track of each animal's
    # position in the pedigree. IT needs to be updated after any
    # movement of founders and before the main loop begins so that
    # the correct indices are use for sires and dams. If you don't
    # have it in the correct place you get duplication of records,
    # inexplicably incorrect parent information, etc.
    orderdict, orderbackdict = {}, {}
    for i in xrange(len(myped)):
        orderdict[myped[i].animalID] = i
        orderbackdict[i] = myped[i].animalID

    while(1):
        if debug:
            print '='*70
            print '[DEBUG]: Pass %s' % ( _passnum )
        # Loop over the pedigree.  Whenever a parent follows their offspring
        # in the pedigree, move the child to the end of the pedigree.
        # Continue until all parents precede their offspring.
        #for i in xrange(l):
        if debug: print '_last_founder: ', _last_founder
        for i in xrange(l):
        #for i in xrange(_last_founder,l):
            #
            # Since attribute access is slower than local variable access we're going
            # to put some IDs in local variables here in the inner loop.
            #
            animalid = myped[i].animalID
            sireid = myped[i].sireID
            damid = myped[i].damID
            animalname = myped[i].name
            sirename = myped[i].sireName
            damname = myped[i].damName

            #print animalid, animalname, sireid, sirename, damid, damname

            _anidx = orderdict[animalid]

            if str(sireid) != str(missingparent) and str(damid) != str(missingparent):
                _maxidx = max(orderdict[sireid], orderdict[damid])
            elif str(sireid) == str(missingparent) and str(damid) != str(missingparent):
                _maxidx = orderdict[damid]
            elif str(sireid) != str(missingparent) and str(damid) == str(missingparent):
                _maxidx = orderdict[sireid]
            else:
                # Handle founders
                _maxidx = -1
            if _anidx < _maxidx:
                _a = copycopy(myped[i])
                # Insert the animal ahead of its parents.
                mypedins(_maxidx+1, _a)
                #if debug:
                    #print 'Moving animal %s (%s) ahead of its parents (sire %s (%s), dam %s (%s).' % ( animalid, animalname, sireid, sirename, damid, damname )
                    #print '\tStarting animal index: ', _anidx
                    #print '\tNew animal index: ', _maxidx+1
                    #if str(sireid) != str(missingparent):
                        #print '\tNew sire index:   ', orderdict[sireid]
                    #if str(damid) != str(missingparent):
                        #print '\tNew dam index:    ', orderdict[damid]
                # Delete the original pedigree entry
                del myped[i]
                for idx in xrange(_anidx, _maxidx):
                    anmov = orderbackdict[idx+1]
                    orderdict[anmov] = idx
                    orderbackdict[idx]  = anmov
                orderdict[animalid] = _maxidx
                orderbackdict[_maxidx] = animalid
                if debug:
                    print 'Moved animal %s (%s) ahead of its parents (sire %s (%s), dam %s (%s).' % ( animalid, animalname, sireid, sirename, damid, damname )
                    print '\tNew animal index: ', orderdict[animalid]
                    if str(sireid) != str(missingparent):
                        print '\tNew sire index:   ', orderdict[sireid]
                    if str(damid) != str(missingparent):
                        print '\tNew dam index:    ', orderdict[damid]
                # Delete the animal's original (first) record in the pedigree file.
                del _a, animalid, sireid, damid, animalname, sirename, damname
                del _anidx, _maxidx
                _moved_counter = _moved_counter + 1

            #elif str(sireid) == str(missingparent) and str(damid) == str(missingparent):
                #if _anidx > 0:
                    #_a = copycopy(myped[i])
                    ## SO NOT move this delete statement or you'll break code!
                    ## The list is being altered by adding items to the head,
                    ## so we need to delete the originalrecord before prepending
                    ## the list. If not, you'll start losing records to deletion
                    ## during reordering.
                    #del myped[i]
                    #mypedins(_last_founder, _a)
                    #for idx in xrange(_last_founder, _anidx):
                        #anmov = orderbackdict[idx]
                        #orderdict[anmov] = idx+1
                        #orderbackdict[idx+1] = anmov
                    #orderdict[animalid] = _last_founder
                    #orderbackdict[_last_founder] = animalid
                    #if debug:
                        #print 'Moved founder %s (%s) to position %s in the pedigree (sire %s (%s), dam %s (%s).' % ( animalid, animalname, _last_founder, sireid, sirename, damid, damname )
                        #print '\tNew animal index: ', orderdict[animalid]
                        #if str(sireid) != str(missingparent):
                            #print '\tNew sire index:   ', orderdict[sireid]
                        #if str(damid) != str(missingparent):
                            #print '\tNew dam index:    ', orderdict[damid]
                    ## Delete the animal's original (first) record in the pedigree file.
                    #del _a, animalid, sireid, damid, animalname, sirename, damname
                    #del _anidx, _maxidx
                    #_moved_counter = _moved_counter + 1
                #else:
                    #if debug:
                        #print 'Animal %s (%s) is already at the beginning of the pedigree' % ( animalid, animalname )
                #_last_founder = _last_founder + 1

            else:
                pass

        if debug:
            for m in myped:
                print m.animalID, m.name, m.sireID, m.sireName, m.damID, m.damName

        if _moved_counter == 0:
            break
        if _passnum == max_rounds:
            logging.error('pyp_utils/reorder() was unable to reorder the pedigree in %s rounds. Subsequent calculations that depend on the pedigree being correctly reordered may produce incorrect answers.' % ( _passnum ))
            print '[ERROR]: pyp_utils/reorder() was unable to reorder the pedigree in %s rounds. Subsequent calculations that depend on the pedigree being correctly reordered may produce incorrect answers.' % ( _passnum )
            break
        else:
            _passnum = _passnum + 1
            _moved_counter = 0

    if io == 'yes':
        # Write the reordered pedigree to a file and return the ordered pedigree.
        # Note that the reordered pedigree is currently only writte in the 'asd'
        # format, regardless of the format of the original file.
        a_outputfile = '%s%s%s' % (filetag,'_reordered','.ped')
        aout = open(a_outputfile,'w')
        aname = '# FILE: %s\n' % (a_outputfile)
        aout.write(aname)
        aout.write('# REORDERED pedigree produced by PyPedal.\n')
        aout.write('% asd\n')
        for l in range(len(myped)):
            aout.write('%s,%s,%s\n' % myped[l].animalID,myped[l].sireID,myped[l].damID)
        aout.close()
        del order

    return myped

##
# fast_reorder() renumbers a pedigree such that parents precede their offspring in
# the pedigree.  In order to minimize overhead as much as is reasonably possible,
# a list of animal IDs that have already been seen is kept.  Whenever a parent
# that is not in the seen list is encountered, the offspring of that parent is
# moved to the end of the pedigree.  This should ensure that the pedigree is
# properly sorted such that all parents precede their offspring.  myped is
# reordered in place.  fast_reorder() uses dictionaries to renumber the pedigree
# based on paddedIDs.
# @param myped A PyPedal pedigree object.
# @param filetag A descriptor prepended to output file names.
# @param io Indicates whether or not to write the reordered pedigree to a file (yes|no).
# @param debug Flag to indicate whether or not debugging messages are written to STDOUT.
# @retval A reordered PyPedal pedigree.
def fast_reorder(myped,filetag='_new_reordered_',io='no',debug=0):
    """
    Renumber a pedigree such that parents precede their offspring in the
    pedigree.  In order to minimize overhead as much as is reasonably possible,
    a list of animal IDs that have already been seen is kept.  Whenever a parent
    that is not in the seen list is encountered, the offspring of that parent is
    moved to the end of the pedigree.  This should ensure that the pedigree is
    properly sorted such that all parents precede their offspring.  myped is
    reordered in place.

    reorder() is VERY slow, but I am pretty sure that it works correctly.  fast_reorder()
    appears to be VERY fast, but I am not sure if it works correctly all of the time or
    not.  Use this procedure at your own risk!
    """

    l = len(myped)
    idlist = []
    animalmap = {}
    # <kludge>
    myped.reverse()
    # </kludge>
    if debug == 1:
        print '\tPedigree contains %s animals.' % (l)
        print '\tMaking a dictionary of animal objects'
        print '\tMaking a list of padded animal IDs'
    for i in range(l):
        if debug == 1:
            print '\tDEBUG\tID %s: %s = %s %s %s' % (i,myped[i].animalID,myped[i].paddedID,myped[i].sireID,myped[i].damID)
        animalmap[myped[i].paddedID] = myped[i]
        idlist.append(int(myped[i].paddedID))
    myped = []
    l = len(idlist)
    if debug == 1:
        print '[DEBUG]: %s elements in idlist' % (l)
        print '[DEBUG]: Printing reordered pedigree...'
    for i in range(len(idlist)):
        myped.append(animalmap[str(idlist[i])])
    if debug == 1:
        print '\t[DEBUG]:\tID %s: %s = %s' % (i,myped[i].animalID,myped[i].paddedID)
    if io == 'yes':
        # Write the reordered pedigree to a file and return the ordered pedigree.
        # Note that the reordered pedigree is currently only written in the 'asd'
        # format, regardless of the format of the original file.
        a_outputfile = '%s%s%s' % (filetag,'_reord','.ped')
        aout = open(a_outputfile,'w')
        aname = '# FILE: %s\n' % (a_outputfile)
        aout.write(aname)
        aout.write('# REORDERED pedigree produced by PyPedal using fast_reorder().\n')
        aout.write('% asd\n')
        for l in range(len(myped)):
            aout.write('%s,%s,%s\n' % myped[l].animalID,myped[l].sireID,myped[l].damID)
        aout.close()
    return myped

##
# renumber() takes a pedigree as input and renumbers it such that the oldest
# animal in the pedigree has an ID of '1' and the n-th animal has an ID of 'n'.  If the
# pedigree is not ordered from oldest to youngest such that all offspring precede their
# offspring, the pedigree will be reordered.  The renumbered pedigree is written to disc in
# 'asd' format and a map file that associates sequential IDs with original IDs is also
# written.
# @param myped A PyPedal pedigree object.
# @param filetag A descriptor prepended to output file names.
# @param io Indicates whether or not to write the renumbered pedigree to a file (yes|no).
# @param outformat Flag to indicate whether or not to write an asd pedigree (0) or a full pedigree (1).
# @param returnmap Indicates whether or not an ID map, as well as the renumbered pedigree, should be returned.  If nonzero, suppresses writing of ID maps to disc.
# @param debug Flag to indicate whether or not progress messages are written to stdout.
# @param missingparent Indicates the value used to indicate a missing parent.
# @param animaltype Type of animal object used to populate pedigree
# @param cleanmap Cleans-up (deletes) the ID map file after renumbering is complete.
# @retval A reordered PyPedal pedigree.
def renumber(myped, filetag='_renumbered_', io='no', outformat='0', debug=0, returnmap=0, missingparent=0, \
    animaltype='new', cleanmap=True):
    """
    renumber() takes a pedigree as input and renumbers it such that the oldest
    animal in the pedigree has an ID of '1' and the n-th animal has an ID of 'n'.  If the
    pedigree is not ordered from oldest to youngest such that all offspring precede their
    offspring, the pedigree will be reordered.  The renumbered pedigree is written to
    disc in 'asd' format and a map file that associates sequential IDs with original IDs is also written.
    """
    if debug == 1:
        print '[DEBUG]: Pedigree of size %s passed to renumber()' % (len(myped))

    # Do we have NewAnimals? They have names and others do not.
    if animaltype == 'new': isnewanimal = 1
    else: isnewanimal = 0

    # In the dictionary id_map, the old IDs are the keys and the
    # new IDs are the values.
    id_map = {}
    idnum = 1       # starting ID number for renumbered IDs
    for l in xrange(len(myped)):
        if debug == 1:
            if l == 0:
                print '[DEBUG]: Renumbering the pedigree...'
            if numpy.fmod(l,10000) == 0:
                print'\t%s ' % (l)
            print '[DEBUG]: An:%s (%s)\tSire: %s\tDam: %s' % (myped[l].animalID,myped[l].paddedID,myped[l].sireID,myped[l].damID)
        id_map[myped[l].animalID] = idnum
        #myped[l].animalID = id_map[myped[l].animalID]
        if debug == 1:
            print '\t[DEBUG]: Renumbering animal from %s to %s (iter %s)' % (myped[l].animalID,idnum,l)
        myped[l].renumberedID = idnum
        myped[l].animalID = idnum
        # If an animal has its original ID as its name, we need
        # to change the name to match the renumbered ID so that
        # pedigree drawings using pyp_graphics/draw_pedigree()
        # will be correctly labelled.
        if isnewanimal:
            if myped[l].name == myped[l].originalID:
                myped[l].name = myped[l].renumberedID
        # We cannot forget to renumber parents, too!
        s = myped[l].sireID
        if str(s) != str(missingparent):
        # This is a hack to deal with offspring that have birthdates which precede their parents'.
            try:
                if debug == 1:
                    print '\t\t[DEBUG]: Renumbering sire from %s to %s' % (s,id_map[s])
                myped[l].sireID = id_map[s]
            except:
                myped[l].sireID = 0
        d = myped[l].damID
        if str(d) != str(missingparent):
        # This is a hack to deal with offspring that have birthdates which precede their parents'.
            try:
                if debug == 1:
                    print '\t\t[DEBUG]: Renumbering dam from %s to %s' % (d,id_map[d])
                myped[l].damID = id_map[d]
            except:
                myped[l].damID = 0
        idnum = idnum + 1
        if debug == 1:
            print '[DEBUG]: animal ID = %s (%s)' % (myped[l].animalID, myped[l].originalID)
            print '[DEBUG]: An:%s\tSire: %s\tDam: %s' % (myped[l].animalID,myped[l].sireID,myped[l].damID)
        #print

    # This next bit renumbers the sons, daus, and unks dictionaries for
    # each animal.
    if isnewanimal:
        _sons, _daus, _unks = {}, {}, {}
        for m in myped:
            # Renumber sons
            for k in m.sons.keys():
                try: _sons[id_map[k]] = k
                except: pass
            m.sons = _sons
            # Renumber daughters
            for k in m.daus.keys():
                try: _daus[id_map[k]] = k
                except: pass
            m.daus = _daus
            # Renumber unknowns
            for k in m.unks.keys():
                try: _unks[id_map[k]] = k
                except: pass
            m.unks = _unks

    if io == 'yes':
        # Write the renumbered pedigree to a file
        ped_outputfile = '%s%s%s' % (filetag,'_renum','.ped')
        pout = open(ped_outputfile,'w')
        pname = '# FILE: %s\n' % (ped_outputfile)
        pout.write(pname)
        pout.write('# RENUMBERED pedigree produced by PyPedal.\n')
        pout.write('% asd\n')
        for l in range(len(myped)):
            if outformat == '0' or outformat == 0:
                pout.write('%s,%s,%s\n' % myped[l].animalID,myped[l].sireID,myped[l].damID)
            else:
                pout.write('%s,%s,%s,%s,%s,%s,%s\n' % myped[l].animalID,myped[l].sireID,myped[l].damID,myped[l].by,myped[l].sex,myped[l].fa,myped[l].gen)
        pout.close()
    if not returnmap:
        # Write the old ID -> new ID mapping to a file
        map_outputfile = '%s%s%s' % (filetag,'_id_map','.map')
        #print '[DEBUG]: ID map file name is %s' % (map_outputfile)
        mout = open(map_outputfile,'w')
        mname = '# FILE: %s\n' % (map_outputfile)
        mout.write(mname)
        mout.write('# Renumbered ID to Old ID mapping produced by PyPedal.\n')
        mout.write('# The lefthand column contains the original IDs.\n')
        mout.write('# The righthand column contains the renumbered IDs.\n')
        mout.write('# Old ID\tRenum ID\n')
        k = id_map.keys()
        v = id_map.values()
        for l in range(len(id_map)):
            mout.write('%s,%s\n' % (k[l],v[l]))
            #print 'Old ID = %s,  New ID = %s' % (k[l],v[l])
        mout.close()
    # Clean-up
    if cleanmap == True:
        delete_id_map(filetag)
    #print 'ID map in renumber():%s' % (id_map)
    if not returnmap:
        return myped
    else:
        return myped, id_map

##
# load_id_map() reads an ID map from the file generated by pyp_utils/renumber()
# into a dictionary.  There is a VERY similar function, pyp_io/id_map_from_file(), that
# is deprecated because it is much more fragile that this procedure.
# @param filetag A descriptor prepended to output file names that is used to determine the input file name.
# @retval A dictionary whose keys are renumbered IDs and whose values are original IDs or an empty dictionary (on failure).
def load_id_map(filetag='_renumbered_'):
    """
    load_id_map() reads an ID map from the file generated by pyp_utils/renumber()
    into a dictionary.  There is a VERY similar function, pyp_io/id_map_from_file(), that
    is deprecated because it is much more fragile that this procedure.
    """
    try:
        _infile = '%s%s%s' % (filetag,'_id_map','.map')
        mapin = open(_infile,'r')
        idmap = {}
        while 1:
            line = mapin.readline()
            if not line:
                break
            else:
                line = string.strip(line[:-1])
                if line[0] == '#':
                    pass
                else:
                    _line = string.split(line,',')
                    if len(_line) != 2:
                        print '[ERROR]: Invalid number of elements in line read from ID map file (%s)' % (_line)
                        break
                    else:
                        idmap[int(_line[1])] = int(_line[0])
        mapin.close()
        return idmap
    except:
        #print '[ERROR]: Could not open the ID map file %s in load_id_map()!' % (_infile)
        #sys.exit(0)
        return {}

##
# delete_id_map() checks to see if an ID map for the given filetag exists.  If the file exists, it is
# deleted.
# @param filetag A descriptor prepended to output file names that is used to determine name of the file to delete.
# @retval A flag indicating whether or not the file was successfully deleted (0|1)
def delete_id_map(filetag='_renumbered_'):
    """
    delete_id_map() checks to see if an ID map for the given filetag exists.  If the file
    exists, it is deleted.
    """
    try:
        _infile = '%s%s%s' % (filetag,'_id_map','.map')
        if _infile in os.listdir('.'):
            os.remove(_infile)
        return 1
    except:
        return 0

##
# trim_pedigree_to_year() takes pedigrees and removes all individuals who were not born
# in birthyear 'year'.
# @param pedobj A PyPedal pedigree object.
# @param year A birthyear.
# @retval A pedigree containing only animals born in the given birthyear or an ampty list (on failure).
def trim_pedigree_to_year(pedobj,year):
    """
    trim_pedigree_to_year() takes pedigrees and removes all individuals who were not born
    in birthyear 'year'.
    """
    # trim_pedigree_to_year() takes pedigrees and removes all individuals
    # who were not born in birthyear 'year'.  The reduced (trimmed) pedigree
    # is returned.
    try:
        indices = []
        modped = pedobj.pedigree[:]
        for l in range(len(modped)):
            if int(modped[l].by) == int(year):
                pass
            else:
                indices.append(l)
        indices.reverse()
        for i in range(len(indices)):
            del modped[indices[i]]
        return modped
    except:
        return []

##
# pedigree_range() takes a renumbered pedigree and removes all individuals
# with a renumbered ID > n.  The reduced pedigree is returned.  Assumes that
# the input pedigree is sorted on animal key in ascending order.
# @param pedobj A PyPedal pedigree object.
# @param n A renumbered animalID.
# @retval A pedigree containing only animals born in the given birthyear of an ampty list (on failure).
def pedigree_range(pedobj, n):
    """
    pedigree_range() takes a renumbered pedigree and removes all individuals
    with a renumbered ID > n.  The reduced pedigree is returned.  Assumes that
    the input pedigree is sorted on animal key in ascending order.
    """
    # pedigree_range() takes a renumbered pedigree and removes all individuals
    # with a renumbered ID > n.  The reduced pedigree is returned.  Assumes that
    # the input pedigree is sorted on animal key in ascending order.
    try:
        modped = []
        for i in range(n):
            modped.append(pedobj.pedigree[i])
            return modped
    except:
        return []

##
# sort_dict_by_keys() returns a dictionary where the values in the dictionary
# in the order obtained by sorting the keys.  Taken from the routine sortedDictValues3
# in the "Python Cookbook", p. 39.
# @param mydict A non-empty Python dictionary.
# @retval The input dictionary with keys sorted in ascending order or an empty dictionary (on failure).
def sort_dict_by_keys(mydict):
    """
    sort_dict_by_keys() returns a dictionary where the values in the dictionary
    in the order obtained by sorting the keys.  Taken from the routine sortedDictValues3
    in the "Python Cookbook", p. 39.
    """
    try:
        if len(mydict) == 0:
            return mydict
        else:
            keys = mydict.keys()
            keys.sort()
            return map(mydict.get, keys)
    except:
        return {}

##
# sort_dict_by_values() returns a dictionary where the keys in the dictionary
# are sorted ascending value, first on value and then on key within value.  The
# implementation was taken from John Hunter's contribution to a newsgroup thread:
# http://groups-beta.google.com/group/comp.lang.python/browse_thread/thread/bbc259f8454e4d3f/cc686f4cd795feb4?q=python+%22sorted+dictionary%22&rnum=1&hl=en#cc686f4cd795feb4
# @param first Python list of dictionary keys.
# @param second Python list of dictionary values.
# @retval A list of tuples sorted in ascending order.
def sort_dict_by_values(first, second):
    """
    sort_dict_by_values() returns a dictionary where the keys in the dictionary
    are sorted ascending value, first on value and then on key within value.  The
    implementation was taken from John Hunter's contribution to a newsgroup thread:
    http://groups-beta.google.com/group/comp.lang.python/browse_thread/thread
    /bbc259f8454e4d3f/cc686f4cd795feb4?q=python+%22sorted+dictionary%22&
    rnum=1&hl=en#cc686f4cd795feb4
    """
    c1 = cmp(first[1], second[1])
    if c1!=0:
        return c1
    return cmp(first[0], second[0])

##
# simple_histogram_dictionary() returns a dictionary containing a simple, text histogram.
# The input dictionary is assumed to contain keys which are distinct levels and values
# that are counts.
# @param mydict A non-empty Python dictionary.
# @param histchar The character used to draw the histogram (default is '*').
# @param histstep Used to determine the number of bins (stars) in the diagram.
# @retval A dictionary containing the histogram by level or an empty dictionary (on failure).
def simple_histogram_dictionary(mydict, histchar='*', histstep=5):
    """
    simple_histogram_dictionary() returns a dictionary containing a simple, text
    histogram.  The input dictionary is assumed to contain keys which are distinct levels
    and values that are counts.
    """
    try:
        hist_dict = {}
        hist_sum = 0.
        if histstep < 0 or histstep > 100:
            histstep = 5
        for k in mydict.keys():
            hist_sum = hist_sum + mydict[k]
        #print '[DEBUG]: %s' % (hist_sum)
        for k in mydict.keys():
            _freq = ( float(mydict[k]) / float(hist_sum) ) * 100.
            _v = around(_freq,0)
            _n_stars = int( around( (_v / float(histstep)),0 ) )
            if _n_stars > 0:
                hist_dict[k] = '%s%s' % (histchar*_n_stars,' '*(20-_n_stars))
            else:
                hist_dict[k] = '%s' % (' '*20)
        return hist_dict
    except:
        return {}

##
# reverse_string() reverses the input string and returns the reversed version.
# @param mystring A non-empty Python string.
# @retval The input string with the order of its characters reversed.
def reverse_string(mystring):
    """
    reverse_string() reverses the input string and returns the reversed version.
    """
    try:
        if len(mystring) < 2:
            return mystring
        else:
            mystringreversed = []
            for l in range(len(mystring)):
                mystringreversed.append(mystring[l])
                mystringreversed.reverse().join()
            return mystringreversed
    except:
        return 0

##
# pyp_nice_time() returns the current date and time formatted as, e.g.,
# Wed Mar 30 10:26:31 2005.
# @retval A string containing the formatted date and time.
def pyp_nice_time():
    """
    pyp_nice_time() returns the current date and time formatted as, e.g.,
    Wed Mar 30 10:26:31 2005.
    """
    try:
        return time.asctime(time.localtime(time.time()))
    except:
        return 0

##
# string_to_table_name() takes an arbitrary string and returns a string that
# is safe to use as an SQLite table name.
# @param instring A string that will be converted to an SQLite-safe table name.
# @retval A string that is safe to use as an SQLite table name.
def string_to_table_name(instring):
    """
    string_to_table_name() takes an arbitrary string and returns a string that
    is safe to use as an SQLite table name.
    """
    try:
        # This list comprehension idea is taken from the Python Cookbook:
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/59857
        allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
        outstring = ''.join([c for c in instring if c in allowed_chars])
        return outstring
    except:
        return instring

##
# pyp_datestamp() returns a datestamp, as a string, of the format
# YYYYMMDDHHMMSS.
# @retval A 14-character string containing the datestamp.
def pyp_datestamp():
    """
    pyp_datestamp() returns a datestamp, as a string, of the format
    YYYYMMDDHHMMSS.
    """
    try:
        #return time.asctime(time.localtime(time.time()))
        return time.strftime('%Y%m%d%H%M%S', (time.localtime(time.time())))
    except:
        return '00000000000000'

##
# subpedigree() takes a NewPedigree object and list of animal
# IDs and returns a NewPedigree object containing only the
# animals in the animals list.
# @param pedobj PyPedal pedigree object.
# @param anlist A list of animal IDs.
# @retval An instance of a NewPedigree object.
def subpedigree(pedobj, anlist):
    """
    subpedigree() takes a NewPedigree object and list of animal
    IDs and returns a NewPedigree object containing only the
    animals in the animals list.
    """
    try:
        NewPed = copy.copy(pedobj)
        order = []
        _tempped = copy.copy(NewPed.pedigree)
        for _p in _tempped:
            order.append(_p.animalID)
        for _p in NewPed.pedigree:
            if _p.animalID not in anlist:
                # Delete the animal from the pedigree and the
                # ID maps.
                _anidx = order.index(_p.animalID)
                del NewPed.namemap[NewPed.namebackmap[NewPed.backmap[_p.animalID]]]
                del NewPed.namebackmap[NewPed.backmap[_p.animalID]]
                del NewPed.idmap[NewPed.backmap[_p.animalID]]
                del NewPed.backmap[_p.animalID]
                del _tempped[_anidx]
                del order[_anidx]
                for _t in _tempped:
                    order.append(_t.animalID)
        # Update the metadata object.
        NewPed.pedigree = _tempped
        del(_tempped)
        del(order)
        NewPed.metadata = pyp_newclasses.PedigreeMetadata(NewPed.pedigree, NewPed.kw)
        # Renumber the pedigree.
        if NewPed.kw['renumber']:
            NewPed.renumber()
        return NewPed
    except:
        return 0

##
# founders_from_list() takes a list of NewAnimal objects and returns a
# list of animalIDs that represent founders in that pedigree (animals
# with an unknown sire and dam.
# @param anlist A list of NewAnimal objects.
# @param unkID The animalID assigned to unknown parents.
# @retval A list of animalIDs of founders.
def founders_from_list(anlist, unkID):
    """
    founders_from_list() takes a list of NewAnimal objects and returns a
    list of animalIDs that represent founders in that pedigree (animals
    with an unknown sire and dam.
    """
    try:
        flist = [x.animalID for x in anlist if x.sireID == unkID and x.damID == unkID]
        return flist
    except:
        return []

##
# founder_allele_dict() takes a pedigree and returns a dictionary containing
# an entry for each unique founder allele.
# @param pedobj A PyPedal pedigree.
# @retval A dictionary whose keys are founder alleles and whose values are 0.0
def founder_allele_dict(pedobj):
    """
    founder_allele_dict() takes a pedigree and returns a dictionary containing
    an entry for each unique founder allele.
    """
    try:
        falist = [pedobj.pedigree[x-1].alleles for x in pedobj.metadata.unique_founder_list]
        fadict = {}
        for fa in falist:
            fadict[fa[0]] = 0.
            fadict[fa[1]] = 0.
        return fadict
    except:
        return {}

##
# founder_allele_map() takes a pedigree and returns a dictionary
# mapping founder alleles to their animal of origin.
# @note I don't remember writing this, so I'm not sure just what I intended it to do. Probably broken.
# @param pedobj A PyPedal pedigree.
# @retval A dictionary whose keys are founder alleles and whose values are the founder of origin.
def founder_allele_map(pedobj):
    """
    founder_allele_map() takes a pedigree and returns a dictionary
    mapping founder alleles to their animal of origin.
    """
    try:
        falist = [pedobj.pedigree[x-1].alleles for x in pedobj.metadata.unique_founder_list]
        fadict = {}
        for fa in falist:
            fadict[fa[0]] = None
            fadict[fa[1]] = None
        fakeys = fadict.keys()
        for fa in fakeys:
            fadict[fa] = fakeys.index(fa)
        return fadict
    except:
        return {}

##
# founder_allele_freq() takes a pedigree and returns a dictionary containing
# an entry for each unique founder allele and the frequency of that allele in
# a list of provided animals.
# @note I don't remember writing this, so I'm not sure just what I intended it to do. Probably broken.
# @param pedobj A PyPedal pedigree.
# @param anlist A list of animals in which to track founder allele frequencies.
# @param allele_map Dictionary mapping founder alleles to their animal of origin.
# @param allele_mat Dictionary counting founder alleles.
# @param column Select the correct column to increment.
# @retval A dictionary whose keys are founder alleles and whose values are frequencies.
def founder_allele_freq(pedobj, anlist, allele_map, allele_mat, column):
    """
    founder_allele_freq() takes a pedigree and returns a dictionary containing
    an entry for each unique founder allele and the frequency of that allele in
    a list of provided animals.
    """
    #try:
    backmap = [pedobj.idmap[an] for an in anlist]
    fafreq = [pedobj.pedigree[an-1].alleles for an in backmap]
    for fa in fafreq:
        row0 = allele_map[fa[0]]
        row1 = allele_map[fa[1]]
        #print '    Adding 1 to row %s, col %s' % ( row0, column )
        allele_mat[row0,column] = allele_mat[row0,column] + 1.
        #print '    Adding 1 to row %s, col %s' % ( row1, column )
        allele_mat[row1,column] = allele_mat[row1,column] + 1.
    return allele_mat
    #except:
    #    return False