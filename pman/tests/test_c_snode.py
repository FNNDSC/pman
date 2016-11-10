from unittest import TestCase

from pman import C_stree

import pudb

class TestCSnode(TestCase):
    def test_csnode_constructor(self):

        aTree = C_stree()
        bTree = C_stree()
        ATree = C_stree()

        aTree.cd('/')
        aTree.mkcd('a')
        aTree.mknode(['b', 'c'])
        aTree.cd('b')
        aTree.touch('file1', 10)
        aTree.touch('file2', "Rudolph Pienaar")
        aTree.touch('file3', ['this', 'is', 'a', 'list'])
        aTree.touch('file4', ('this', 'is', 'a', 'tuple'))
        aTree.touch('file5', {'name': 'rudolph', 'address': '505 Washington'})

        aTree.mknode(['d', 'e'])
        aTree.cd('d')
        aTree.mknode(['h', 'i'])
        aTree.cd('/a/b/e')
        aTree.mknode(['j', 'k'])
        aTree.cd('/a/c')
        aTree.mknode(['f', 'g'])
        aTree.cd('f')
        aTree.mknode(['l', 'm'])
        aTree.cd('/a/c/g')
        aTree.mknode(['n', 'o'])

        ATree.cd('/')
        ATree.mkcd('A')
        ATree.mknode(['B', 'C'])
        ATree.cd('B')
        ATree.mknode(['D', 'E'])
        ATree.cd('D')
        ATree.mknode(['H', 'I'])
        ATree.cd('/A/B/E')
        ATree.mknode(['J', 'K'])
        ATree.cd('/A/B/E/K')
        ATree.touch('file1', 11)
        ATree.touch('file2', "Reza Pienaar")
        ATree.touch('file3', ['this', 'is', 'another', 'list'])
        ATree.touch('file4', ('this', 'is', 'another', 'tuple'))
        ATree.touch('file5', {'name': 'reza', 'address': '505 Washington'})
        ATree.cd('/A/C')
        ATree.mknode(['F', 'G'])
        ATree.cd('F')
        ATree.mknode(['L', 'M'])
        ATree.cd('/A/C/G')
        ATree.mknode(['N', 'O'])

        bTree.cd('/')
        bTree.mkcd('1')
        bTree.mknode(['2', '3'])
        bTree.cd('2')
        bTree.mknode(['4', '5'])
        bTree.cd('4')
        bTree.mknode(['8', '9'])
        bTree.cd('/1/2/5')
        bTree.mknode(['10', '11'])
        bTree.cd('/1/3')
        bTree.mknode(['6', '7'])
        bTree.cd('6')
        bTree.mknode(['12', '13'])
        bTree.cd('/1/3/7')
        bTree.mknode(['14', '15'])

        aTree.tree_metaData_print(False)
        ATree.tree_metaData_print(False)
        bTree.tree_metaData_print(False)

        print('aTree = %s' % aTree)
        # print(aTree.pathFromHere_walk('/'))
        print('ATree = %s' % ATree)
        # print(ATree.pathFromHere_walk('/'))
        print('bTree = %s' % bTree)
        # print(bTree.pathFromHere_walk('/'))

        aTree.cd('/')
        aTree.graft(bTree, '/1/2/')
        aTree.tree_metaData_print(False)
        print('aTree = %s' % aTree)
        # print(aTree.pathFromHere_walk('/'))
        # print(aTree.l_allPaths)

        bTree.cd('/1/2/4/9')
        bTree.graft(ATree, '/A/B')
        bTree.tree_metaData_print(False)
        print('bTree = %s' % bTree)
        # print(bTree.pathFromHere_walk('/'))
        # print(bTree.l_allPaths)

        print('aTree = %s' % aTree)
        # print(aTree.pathFromHere_explore('/'))
        # print(aTree.l_allPaths)
        # print(aTree.filesFromHere_explore('/'))
        # print(aTree.l_allFiles)

        print('Saving bTree...')
        bTree.tree_save(startPath       = '/',
                        pathDiskRoot    = '/tmp/bTree',
                        failOnDirExist  = True,
                        saveJSON        = True,
                        savePickle      = False)

        print('Saving aTree...')
        aTree.tree_save(startPath       = '/',
                        pathDiskRoot    = '/tmp/aTree',
                        failOnDirExist  = True,
                        saveJSON        = True,
                        savePickle      = False)

        # pudb.set_trace()
        print('Reading aTree into cTree...')
        cTree = C_stree.tree_load(
                        pathDiskRoot    = '/tmp/aTree',
                        loadJSON        = True,
                        loadPickle      = False)
        cTree.tree_metaData_print(False)
        print('cTree = %s' % cTree)
        cTree.rm('/4/9/B/E/K/file1')
        print('cTree = %s' % cTree)
        cTree.rm('/4/9/B/E/K/file2')
        print('cTree = %s' % cTree)
        cTree.rm('/4/9/B/E/K')
        print('cTree = %s' % cTree)

        dTree   = C_stree()
        cTree.tree_copy(startPath   = '/a/b/file5',
                        destination = dTree)
        print('dTree = %s' % dTree)
