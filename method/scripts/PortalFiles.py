# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import argparse
import csv
import gzip
import itertools
import os
import random
import time

# Constants
# The expected header
c_CELL_ID = "cell"
c_COORDINATES_HEADER = ["NAME", "X", "Y"]
c_COORDINATES_OPTIONAL_Z = "Z"
c_COORDINATES_HEADER_LENGTH = len(c_COORDINATES_HEADER)
c_DEFAULT_DELIM = "\t"
c_DEID_POSTFIX = "_deidentifed"
c_EXPRESSION_00_ELEMENT = "GENE"
c_GENE_LIST_00_ELEMENT = "GENE NAMES"
c_MAP_DELIM = "\t->\t"
c_MAP_POSTFIX = "_mapping"
c_METADATA_00_ELEMENT = "NAME"
c_REPORT_LINE_NUMBER_BLOCK = 500
c_SUBSET_POSTFIX = "_subset"
c_TYPE_HEADER_ID = "TYPE"
c_TYPE_NUMERIC = "numeric"
c_TYPE_GROUP = "group"
c_VALID_TYPES = [c_TYPE_NUMERIC, c_TYPE_GROUP]

# Demo links
c_METADATA_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/metadata_example.txt"
c_COORDINATES_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/coordinates_example.txt"
c_EXPRESSION_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/expression_example.txt"
c_GENELIST_DEMO_LINK = "https://github.com/broadinstitute/single_cell_portal/blob/master/demo_data/genelist_example.txt"

coordinates_file_has_error = False
coordinates_cell_names = []

metadata_file_has_error = False
metadata_cell_names = []

expression_file_has_error = False
expression_cell_names = []


class ParentPortalFile:

    def __init__(self, file_name,
                 file_delimiter,
                 has_type=True,
                 expected_header=None,
                 demo_file_link=None):
        """
        Create object. This is an objec that must be inherited
        due to abstract methods that are not implemented.
        Tested
        """
        self.file_has_error = False
        self.delimiter = file_delimiter
        self.demo_file = demo_file_link
        self.expected_header = expected_header
        self.expected_header_length = len(expected_header) if expected_header else 0
        self.file_name = os.path.abspath(file_name)
        init_handle = self.csv_handle
        self.header = next(init_handle)
        self.type_header = next(init_handle) if has_type else None
        self.header_length = len(self.header)
        self.line_number = 1
        self.cell_names = None

    @property
    def csv_handle(self):
        """
        When the csv handle is given it is a
        fresh handle at the beginning of the file.
        Tested
        """

        file_handle = None
        if ".gz" == os.path.splitext(self.file_name)[-1]:
            file_handle = gzip.open(self.file_name, 'rt')
        else:
            file_handle = open(self.file_name, 'r')
        return(csv.reader(file_handle, delimiter=self.delimiter))

    @abc.abstractmethod
    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Must be over written per file given files have different formats.
        """
        return()

    @abc.abstractmethod
    def check_body(self):
        """
        Check body of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Must be over written per file given files have different formats.
        """
        return()

    def check(self):
        """
        Checks the header and body of the file.
        Tested
        """
        print("Checking " + self.file_name)
        self.check_header()
        self.check_body()
        self.check_duplicate_cell_names()
        if self.file_has_error and self.demo_file:
            print(" ".join(["Error!\tThe provided file \"",
                            self.file_name,
                            "\"had errors.",
                            "An example file can be found at",
                            self.demo_file]))
        return(self.file_has_error)

    def get_duplicates(self, items):
        """
        Returns duplicates from an interable.
        Tested
        """
        visited = set()
        duplicates = set()
        for item in items:
            if item in visited:
                duplicates.add(item)
            else:
                visited.add(item)
        return(duplicates)

    def check_duplicate_cell_names(self):
        """
        Check for duplicate cell names.
        Tested
        """
        cell_count = len(self.cell_names)
        if cell_count != len(set(self.cell_names)):
            print(" ".join(["Error!\t",
                            self.file_name,
                            "file has duplicate cell names:"] + list(self.get_duplicates(self.cell_names))))
            self.file_has_error = True
        return(self.file_has_error)

    def check_type_row(self):
        """
        Check a row of types
        Tested
        """
        # Check the length
        if self.header_length != len(self.type_header):
            self.file_has_error = True
            print(" ".join(["Error!\tExpected a type row length of",
                            str(self.header_length),
                            "but received a length of",
                            str(len(self.type_header))]))
        # Check the type header
        if self.type_header[0] != c_TYPE_HEADER_ID:
            self.file_has_error = True
            print(" ".join(["Error!\tExpected the ID for",
                            "the second header row to be",
                            c_TYPE_HEADER_ID,
                            "but was instead",
                            self.type_header[0],
                            "please update."]))
        # Check the type values
        incorrect_types = []
        for type_token in self.type_header[1:]:
            if not type_token in c_VALID_TYPES:
                incorrect_types.append(type_token)
                self.file_has_error = True
        if incorrect_types:
            print(" ".join(["Error!\tThe following types are not recognized:",
                            ",".join(incorrect_types), ".",
                            "Please use any of the following types:",
                            ",".join(c_VALID_TYPES), "."]))
        return(self.file_has_error)

    def compare_cell_names(self, portal_file):
        """
        Check cell names of this portal file wih another.
        Tested
        """
        print(" ".join(["Comparing", self.file_name,
                        "vs", portal_file.file_name]))
        compare_error = False
        if len(self.cell_names) != len(portal_file.cell_names):
            compare_error = True
            print(" ".join(["Error!\tExpected the same number of cells in the",
                            "files but this is not true.",
                            self.file_name, "had",
                            str(len(self.cell_names)), "unique cells.",
                            portal_file.file_name, "had",
                            str(len(portal_file.cell_names)),
                            "unique cells."]))
        # Check composition of lists
        difference = set(self.cell_names) - set(portal_file.cell_names)
        if len(difference) > 0:
            compare_error = True
            print(" ".join(["Gene names unique to",
                            self.file_name,
                            ":"]+list(difference)))
        difference = set(portal_file.cell_names) - set(self.cell_names)
        if len(difference) > 0:
            compare_error = True
            print(" ".join(["Gene names unique to",
                            portal_file.file_name,
                            ":"]+list(difference)))
        return(compare_error)

    def create_safe_file_name(self,file_name):
        """
        Using a given file name
        create a new file name that is unique
        so collisions do not occur.
        """

        if not file_name:
            return(None)

        file_pieces = file_name.split(".")
        file_base = file_pieces[0]
        file_ext = ".".join(file_pieces[1:])
        current_time = time.strftime("%Y_%m_%d_%H_%M_%S",time.gmtime())
        new_file_name = file_base + "_" + current_time + "." + file_ext

        if os.path.exists(new_file_name):
            print(" ".join(["ERROR!\tCan not find a safe file name, ",
                            "the file to be written already exists. ",
                            "Please move or rename the file:",
                            os.path.abspath(new_file_name)]))
            return(None)
        return(new_file_name)

    def get_write_handle(self,new_file_name):
        """
        Get a gzip or standard handle to a file with write functionality.
        """

        if os.path.splitext(self.file_name)[-1] == ".gz":
            return(gzip.open(new_file_name,"wt"))
        else:
            return(open(new_file_name, 'wb'))

    def tag_file_name(self,tag):
        """
        Add a tag to a file name and return a safe version of the file name.
        """

        if not tag:
            return(None)

        file_pieces = self.file_name.split(".")
        file_base = file_pieces[0]
        file_ext = ".".join(file_pieces[1:])
        new_file = file_base + tag + "." + file_ext
        return(self.create_safe_file_name(new_file))

    @abc.abstractmethod
    def subset_cells(self, reduce_cells):
        """
        Reduce file to a subset of cells.
        Must be over written per file given files have different formats.
        """
        return()

    def update_cell_names(self):
        """
        Update cell names from file.
        Tested
        """
        if not self.cell_names:
            self.cell_names = [line[0] for line in self.csv_handle][2:]

    @abc.abstractmethod
    def deidentify_cell_names(self):
        return()

    def __str__(self):
        """
        Create string representation of object.
        Tested
        """
        contents = []
        contents.append("Error:"+str(self.file_has_error))
        contents.append("Delim:"+str(self.delimiter))
        contents.append("Demo:"+str(self.demo_file))
        contents.append("ExpectedHeader:"+",".join(self.expected_header))
        contents.append("ExpectedHeaderLen:"+str(self.expected_header_length))
        contents.append("FileName:"+self.file_name)
        contents.append("Header:"+",".join(self.header))
        contents.append("HeaderLen:"+str(self.header_length))
        contents.append("LineNumber:"+str(self.line_number))
        contents.append("CellNames:"+str(self.cell_names))
        return("; ".join(contents))

class GeneListFile(ParentPortalFile):

    def __init__(self, file_name,
                 file_delimiter=c_DEFAULT_DELIM,
                 demo_file_link=c_GENELIST_DEMO_LINK):
        """
        Represents a gene list file used for visualization in the portal.
        Used in test
        """
        ParentPortalFile.__init__(self, file_name,
                                  file_delimiter,
                                  has_type=False,
                                  expected_header=None,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        if self.header[0] != c_GENE_LIST_00_ELEMENT:
            self.file_has_error = True
            print("".join(["Error!\tExpected the column value \"",
                           c_GENE_LIST_00_ELEMENT,
                           "\" but received \"",
                           self.header[0], "\"."]))

    def check_body(self):
        """
        Check body of file.
        Tested
        """
        check_handle = self.csv_handle
        # Need to skip the header row
        next(check_handle)
        for file_line in check_handle:
            self.line_number += 1
            if len(file_line) != self.header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine:",
                                str(self.line_number),
                                "Expected", str(self.header_length),
                                "columns but received",
                                str(len(file_line)), "."]))
            for token in range(1,len(file_line)):
                if not file_line[token]:
                    self.file_has_error = True
                    print(" ".join(["Expected a value for entry: line",
                                    str(self.line_number+1), ", element",
                                    str(token+1)]))
                else:
                    try:
                        float(file_line[token])
                    except ValueError:
                        self.file_has_error = True
                        print(" ".join(["Error!\tUnexpected type. Line:",
                                        str(self.line_number),
                                        "Value:", file_line[token],
                                        "Expected to be a numeric value."]))

    def compare_gene_names(self,expression_file=None):
        """
        Compare that the genes in the gene list are in the expression file.
        Tested
        """
        if expression_file is None:
            self.file_has_error = True
            print("None expression file was given so no checking could occur.")

        if expression_file:
            exp_genes = expression_file.get_gene_names()
            for gene in self.get_gene_names():
                if gene not in exp_genes:
                    self.file_has_error = True
                    print(" ".join([gene,
                                    "is a gene in the genelist file",
                                    "but not found in the expression file."]))

    def compare_cluster_labels(self,metadata_file=None):
        """
        Compare that the cluster labels in the gene list
        file are in the supplied metadata file.
        Tested
        """
        if metadata_file is None:
            self.file_has_error = True
            print("None metadata file was given so no checking could occur.")

        if metadata_file:
            metadata_labels = metadata_file.get_labels()
            gene_labels = self.get_labels()
            for gene_label in gene_labels:
                if gene_label not in metadata_labels:
                    self.file_has_error = True
                    print(" ".join(["The following group/cluster",
                                    "label was not found in the",
                                    "metadata file:",
                                    gene_label]))

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names which should not exist in this file type so
        a warning for calling the method is given saying cells names
        are not included but nothing else is done.
        Tested
        """
        print(" ".join(["Please note the gene lists should not",
                        "have cell names so no deidentification is needed."]))
        return({"name": None, "mapping": None})

    def get_gene_names(self):
        """
        Returns the gene names in the file.
        Tested
        """
        check_handle = self.csv_handle
        # Need to skip the 2 header rows
        next(check_handle)
        return([file_line[0] for file_line in check_handle])

    def get_labels(self):
        """
        Returns all cluster/group names in the file as unique value.
        Test
        """
        return(list(set(self.header[1:])))

class MetadataFile(ParentPortalFile):

    def __init__(self, file_name,
                 file_delimiter=c_DEFAULT_DELIM,
                 expected_header=None,
                 demo_file_link=c_METADATA_DEMO_LINK):
        """
        Represents a metadata file used for visualization in the portal.
        Tested
        """
        ParentPortalFile.__init__(self, file_name,
                                  file_delimiter,
                                  has_type=True,
                                  expected_header=expected_header,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """

        # Check the minimal header
        if self.header[0] != c_METADATA_00_ELEMENT:
            self.file_has_error = True
            print(" ".join(["Error!\tExpected the first row,",
                            "first column element to be",
                            c_METADATA_00_ELEMENT]))
        if len(self.header) < 2:
            self.file_has_error = True
            print(" ".join(["Error!\tInvalid metadata file.",
                            "Need atleast a cell ID column",
                            "and 1 metadata column"]))
        # Check that the metadata are unique.
        duplicates = self.get_duplicates(self.header)
        if len(duplicates):
            self.file_has_error = True
            print(" ".join(["Error!\tDuplicate metadata were found",
                  "in your header of your metadata file.",
                  "The duplicate headers are:",
                  ",".join(duplicates)]))
        # Check type row
        self.check_type_row()
        return(self.file_has_error)

    def check_body(self):
        """
        Check body of file.
        Tested
        """
        check_handle = self.csv_handle
        # Need to skip the 2 header rows
        next(check_handle)
        next(check_handle)
        type_checks = [ float if type_value == c_TYPE_NUMERIC else str for type_value in self.type_header ]
        for file_line in check_handle:
            self.line_number += 1
            if len(file_line) != self.header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine:",
                                str(self.line_number),
                                "Expected", str(self.header_length),
                                "columns but received",
                                str(len(file_line)), "."]))
            for token in range(len(file_line)):
                if not file_line[token]:
                    self.file_has_error = True
                    print(" ".join(["Expected a value for entry: line",
                                    str(self.line_number+1), ", element",
                                    str(token+1)]))
                elif file_line[token] not in ["NA","nA","Na","na"]:
                    try:
                        type_checks[token](file_line[token])
                    except ValueError:
                        self.file_has_error = True
                        print(file_line[token])
                        print(" ".join(["Error!\tUnexpected type. Line:",
                                        str(self.line_number),
                                        "Value:", file_line[token],
                                        "Expected Type:", self.type_header[token]]))

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names. Create a new file that is deidentified and
        write a mapping file of the names. Do not change the original file.
        If cell names is given, those mappings will be used.
        Tested
        """
        new_file_lines = []
        self.update_cell_names()
        update_names = {c_METADATA_00_ELEMENT: c_METADATA_00_ELEMENT,
                        c_TYPE_HEADER_ID: c_TYPE_HEADER_ID}
        if not cell_names_change:
            cell_names_change = {}
        if not len(cell_names_change):
            for name in self.cell_names:
                cell_names_change.setdefault(name,
                                             "_".join([c_CELL_ID,
                                                       str(len(cell_names_change))]))
        update_names.update(cell_names_change)

        new_deid_file = self.tag_file_name(c_DEID_POSTFIX)
        if new_deid_file is None:
            return(None)
        # Mapping file, check to make sure it does not exist
        new_mapping_file = deid_file_name + c_MAP_POSTFIX + deid_file_ext
        new_mapping_file = self.create_safe_file_name(new_mapping_file)
        if new_mapping_file is None:
            return(None)
        # Write deidentified file
        with open(new_deid_file, 'w') as deid_file:
            write_deid = self.csv_handle
            for file_line in write_deid:
                new_file_lines.append(self.delimiter.join([update_names[file_line[0]]]+file_line[1:]))
            deid_file.write("\n".join(new_file_lines))
        # Write mapping file
        with open(new_mapping_file, 'w') as map_file:
            map_file.write("\n".join(sorted([name_key+c_MAP_DELIM+name_value
                                      for name_key, name_value
                                      in update_names.items()])))
        return({"name": new_deid_file, "mapping": cell_names_change, "mapping_file": new_mapping_file})

    def get_labels(self):
        """
        Get all the labels for all the metadata returned as a unique values.
        Tested
        """
        labels = []
        check_handle = self.csv_handle
        # Need to skip the 2 header rows
        next(check_handle)
        column_types = next(check_handle)
        type_idx = [col_type == c_TYPE_GROUP for col_type in column_types]
        for file_line in check_handle:
            labels.extend(list(itertools.compress(file_line,type_idx)))
            labels = list(set(labels))
        return(labels)

    def subset_cells(self, keep_cells):
        """
        Write a file reduce to just the given cells
        """

        keep_cells = set(keep_cells)
        subset_file_name = self.tag_file_name(c_SUBSET_POSTFIX)
        if subset_file_name is None:
            return(None)

        with open(subset_file_name,"w") as csvwriter:
            file_writer = csv.writer(csvwriter, delimiter=self.delimiter)
            check_handle = self.csv_handle
            # Need to add the 2 header rows
            file_writer.writerow(next(check_handle))
            file_writer.writerow(next(check_handle))
            for file_line in check_handle:
                if file_line[0] in keep_cells:
                    file_writer.writerow(file_line)
        return(subset_file_name)

    def select_subsample_cells(self, number, metadata):
        """
        Randomly subsample cells within a given metadata for a total number of cells.
        Return a list of cells to keep.
        """

        selected = []
        subsample_handle = self.csv_handle
        subsample_header = next(subsample_handle)
        next(subsample_handle)
        try:
            metadata_index = subsample_header.index(metadata)
        except:
            print("Not able to find that metadata group in the header of the metadata file.")
            print("No subsampling will occur.")
            return(selected)

        if metadata_index < 0:
            print( "Could not file the metadata \'"+metadata+"\'to subsample with; no subsampling performed." )
            return(None)
        else:
            # Store rows by metadata value
            rows_by_metadata = dict()
            for entries in subsample_handle:
                metadatum = entries[metadata_index]
                if metadatum in rows_by_metadata:
                    rows_by_metadata[metadatum].append(entries[0])
                else:
                    rows_by_metadata[metadatum] = [entries[0]]

            # Calculate number of metadata to sample.
            number_metadata_values = len(rows_by_metadata.keys())
            sample_amount = int(round(number/number_metadata_values))

            # Sample cells within each metadata value
            for value_list in rows_by_metadata.values():
                selected.extend(random.sample(value_list,sample_amount))
        return(selected)

class CoordinatesFile(ParentPortalFile):

    def __init__(self, file_name,
                 file_delimiter=c_DEFAULT_DELIM,
                 expected_header=c_COORDINATES_HEADER,
                 demo_file_link=c_COORDINATES_DEMO_LINK):
        """
        Represents a coordinate file used for visualizations in the portal.
        Tested
        """
        ParentPortalFile.__init__(self, file_name,
                                  file_delimiter,
                                  has_type=True,
                                  expected_header=expected_header,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        # Check the minimal header
        if len(self.expected_header) > self.header_length:
            self.file_has_error = True
            print(" ".join(["Error!\tExpected to receive a file with",
                            "ateast", str(len(self.expected_header)),
                            "columns. Instead received",
                            str(self.header_length), "columns."]))
        # Check the header is correct for the required section
        if self.expected_header:
            for idx in range(0, len(self.expected_header)):
                if self.header[idx] != self.expected_header[idx]:
                    self.file_has_error = True
                    print("".join(["Error!\tExpected the column value \"",
                                   self.expected_header[idx],
                                   "\" but received \"",
                                   self.header[idx], "\"."]))
        # Check for Z coordinates and if so give feed back for 3D
        if c_COORDINATES_OPTIONAL_Z in self.header:
            print(" ".join(["Note: You included a Z coordinate",
                            "in the file:",
                            self.file_name,
                            "expect a 3D plot to be",
                            "generated from this file."]))
        # Check that the coordinates metadata are unique.
        duplicates = self.get_duplicates(self.header)
        if len(duplicates):
            self.file_has_error = True
            print(" ".join(["Error!\tDuplicate metadata were found",
                  "in your header of your metadata file.",
                  "The duplicate headers are:",
                  ",".join(duplicates)]))
        # Check type row
        self.check_type_row()
        return(self.file_has_error)

    def check_body(self):
        """
        Check body of file.
        Tested
        """

        check_handle = self.csv_handle
        # Need to skip the 2 header rows
        next(check_handle)
        next(check_handle)
        type_checks = [ float if type_value == c_TYPE_NUMERIC else str for type_value in self.type_header ]
        for file_line in check_handle:
            self.line_number += 1
            if len(file_line) != self.header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine:",
                                str(self.line_number),
                                "Expected", str(self.header_length),
                                "columns but received",
                                str(len(file_line)), "."]))
            for token in range(0,len(file_line)):
                try:
                    type_checks[token](file_line[token])
                except ValueError:
                    self.file_has_error = True
                    print(" ".join(["Error!\tUnexpected type. Line:",
                                    str(self.line_number),
                                    "Value:", file_line[token],
                                    "Expected Type:", self.type_header[token]]))

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names. Create a new file that is deidentified and
        write a mapping file of the names. Do not change the original file.
        If cell names is given, those mappings will be used.
        Tested
        """
        new_file_lines = []
        self.update_cell_names()
        update_names = {c_COORDINATES_HEADER[0]: c_COORDINATES_HEADER[0],
                        c_TYPE_HEADER_ID: c_TYPE_HEADER_ID}
        if not cell_names_change:
            cell_names_change = {}
        if not len(cell_names_change):
            for name in self.cell_names:
                cell_names_change.setdefault(name,
                                             "_".join([c_CELL_ID,
                                                       str(len(cell_names_change))]))
        update_names.update(cell_names_change)
        new_deid_file = self.tag_file_name(c_DEID_POSTFIX)
        if new_deid_file is None:
            return(None)
        # Mapping file, check to make sure it does not exist
        new_mapping_file = deid_file_name + c_MAP_POSTFIX + deid_file_ext
        new_mapping_file = self.create_safe_file_name(new_mapping_file)
        if new_mapping_file is None:
            return(None)
        # Write deidentified file
        with open(new_deid_file, 'w') as deid_file:
            write_deid = self.csv_handle
            for file_line in write_deid:
                new_file_lines.append(self.delimiter.join([update_names[file_line[0]]]+file_line[1:]))
            deid_file.write("\n".join(new_file_lines))
        # Write mapping file
        with open(new_mapping_file, 'w') as map_file:
            map_file.write("\n".join(sorted([name_key+c_MAP_DELIM+name_value
                                      for name_key, name_value
                                      in update_names.items()])))
        return({"name": new_deid_file, "mapping": cell_names_change, "mapping_file": new_mapping_file})

    def subset_cells(self, keep_cells):
        """
        Write a file reduce to just the given cells
        """

        keep_cells = set(keep_cells)
        subset_file_name = self.tag_file_name(c_SUBSET_POSTFIX)
        if subset_file_name is None:
            return(None)

        with open(subset_file_name,"w") as filewriter:
            csvwriter = csv.writer(filewriter, delimiter=self.delimiter)
            orig_handle = self.csv_handle
            # Need to add the 2 header rows
            csvwriter.writerow(next(orig_handle))
            csvwriter.writerow(next(orig_handle))
            for file_line in orig_handle:
                if file_line[0] in keep_cells:
                    csvwriter.writerow(file_line)
        return(subset_file_name)

class ExpressionFile(ParentPortalFile):

    def __init__(self, file_name,
                 file_delimiter=c_DEFAULT_DELIM,
                 demo_file_link=c_EXPRESSION_DEMO_LINK):
        """
        Represents an expression file holding measurements.
        Tested
        """
        ParentPortalFile.__init__(self, file_name,
                                  file_delimiter,
                                  has_type=False,
                                  expected_header=None,
                                  demo_file_link=demo_file_link)
        self.update_cell_names()

    def add_expression_header_keyword(self):
        """
        If the matrix is lacking a 0,0 element, add it.
        """

        if self.header[0] != c_EXPRESSION_00_ELEMENT:
            this_hndl = self.csv_handle
            header = this_hndl.next()
            row_1 = this_hndl.next()
            if len(header) + 1 == len(row_1):
                updated_file = self.create_safe_file_name(self.file_name)
                print("Updating file to have the expression 0,0 element.")
                print("Writing new file"+updated_file+", did not affect input files.")
                self.header = [c_EXPRESSION_00_ELEMENT]+self.header
                self.header_length = len(self.header)
                with self.get_write_handle(updated_file) as hnld_correct:
                    csv_correct = csv.writer(hnld_correct,delimiter=self.delimiter)
                    csv_correct.writerow(self.header)
                    csv_correct.writerow(row_1)
                    csv_correct.writerows([row for row in this_hndl])

    def check_header(self):
        """
        Check header of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        if self.header[0] != c_EXPRESSION_00_ELEMENT:
            self.file_has_error = True
            print(" ".join(["Error!\tExpected the first column,",
                            "first row position to be",
                            c_EXPRESSION_00_ELEMENT,
                            "but is was", self.header[0], "."]))

    def check_body(self):
        """
        Check body of the file. If an error occurs set the object
        indicate an error occured. (file_has_error attribute).
        Tested
        """
        check_handle = self.csv_handle
        # Need to skip the header
        next(check_handle)
        for file_line in check_handle:
            self.line_number += 1
            if len(file_line) != self.header_length:
                self.file_has_error = True
                print(" ".join(["Error!\tLine: ",
                                str(self.line_number),
                                ". Expected", str(self.header_length),
                                "columns but received",
                                str(len(file_line)), "."]))

            for token in file_line[1:]:
                try:
                    float(token)
                except ValueError:
                    self.file_has_error = True
                    print(" ".join(["Error!\tLine: ",
                                    str(self.line_number),
                                    ". Unexpected value: ",
                                    token, "."]))
            if self.line_number % c_REPORT_LINE_NUMBER_BLOCK == 0:
                print("    Process update: Line " + str(self.line_number))

    def update_cell_names(self):
        """
        Update cell names from file.
        Tested
        """
        if not self.cell_names:
            self.cell_names = self.header[1:self.header_length+1]

    def deidentify_cell_names(self, cell_names_change=None):
        """
        Deidentify cell names. Create a new file that is deidentified and
        write a mapping file of the names. Do not change the original file.
        If cell names is given, those mappings will be used.
        Tested
        """
        new_file_lines = []
        self.update_cell_names()
        update_names = {c_EXPRESSION_00_ELEMENT: c_EXPRESSION_00_ELEMENT}
        if not cell_names_change:
            cell_names_change = {}
        if not len(cell_names_change):
            for name in self.cell_names:
                cell_names_change.setdefault(name,
                                             "_".join([c_CELL_ID,
                                                       str(len(cell_names_change))]))
        update_names.update(cell_names_change)

        deid_file_pieces = self.file_name.split(".")
        deid_file_name = deid_file_pieces[0]
        deid_file_ext = ".".join(deid_file_pieces[1:])
        # New deidentified file, check to make sure it does not exist
        new_deid_file = deid_file_name + c_DEID_POSTFIX + "." + deid_file_ext
        new_deid_file = self.create_safe_file_name(new_deid_file)

        if new_deid_file is None:
            return(None)
        # Mapping file, check to make sure it does not exist
        new_mapping_file = deid_file_name + c_MAP_POSTFIX + deid_file_ext
        new_mapping_file = self.create_safe_file_name(new_mapping_file)
        if new_mapping_file is None:
            return(None)

        # Write deidentified file
        with self.get_write_handle(new_deid_file) as deid_file:
            write_deid = self.csv_handle
            new_file_lines.append(self.delimiter.join([update_names[name]
                                  for name in next(write_deid)]))
            for file_line in write_deid:
                new_file_lines.append(self.delimiter.join(file_line))
            deid_file.write("\n".join(new_file_lines))

        # Write mapping file
        with open(new_mapping_file, 'w') as map_file:
            map_file.write("\n".join(sorted([name_key+c_MAP_DELIM+name_value
                                      for name_key, name_value
                                      in update_names.items()])))
        return({"name": new_deid_file, "mapping": cell_names_change, "mapping_file": new_mapping_file})

    def get_gene_names(self):
        """
        Returns the gene names in the file.
        Tested
        """
        check_handle = self.csv_handle
        # Need to skip the 2 header rows
        next(check_handle)
        return([file_line[0] for file_line in check_handle])

    def subset_cells(self, keep_cells):
        """
        Write a file reduced to just the given cells
        """

        keep_cells = set(keep_cells)
        subset_file_name = self.tag_file_name(c_SUBSET_POSTFIX)
        if subset_file_name is None:
            return(None)

        with self.get_write_handle(subset_file_name) as file_writer:
            csv_writer = csv.writer(file_writer, delimiter=self.delimiter)
            check_handle = self.csv_handle
            keep_cells.add(c_EXPRESSION_00_ELEMENT)
            header = next(check_handle)
            row_1 = next(check_handle)
            if (len(header) == (len(row_1) - 1)) and (c_EXPRESSION_00_ELEMENT not in header):
                header = [c_EXPRESSION_00_ELEMENT] + header
            header_index = [cell in keep_cells for cell in header]
            # Need to add the header rows
            csv_writer.writerow(list(itertools.compress(header,header_index)))
            csv_writer.writerow(list(itertools.compress(row_1,header_index)))
            for file_line in check_handle:
                csv_writer.writerow(list(itertools.compress(file_line,header_index)))
        return(subset_file_name)
