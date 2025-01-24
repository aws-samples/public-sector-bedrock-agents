# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import re
from typing import Optional, Union, Dict, List
from math import ceil
import json

ReportType = Dict[str, Union[str, int]]

class ArtifactUtils:
    """
    A class to manage AWS Artifact reports.
    """

    def __init__(self) -> None:
        """
        Initialize an ArtifactUtils instance.
        """
        self.client = boto3.client('artifact')
        self.paginator = self.client.get_paginator('list_reports')

    def list_reports(self, page_size: int = 10, page_number: Optional[int] = None) -> List[ReportType]:
        """
        List available reports with pagination.

        Args:
            page_size (int, optional): The number of reports to return per page. Defaults to 10.
            page_number (int, optional): The page number to retrieve. If not provided, the first page is returned.

        Returns:
            List[ReportType]: A list of dictionaries containing report details.
        """
        default_max_results = 10

        if page_size is not None and page_size > default_max_results:
            raise ValueError(f"page_size cannot exceed {default_max_results}")
            
        reports: List[ReportType] = []
        paginator = self.paginator.paginate(PaginationConfig={'PageSize': page_size})
        page_iterator = iter(paginator)

        if page_number is None or page_number == 1:
            page = next(page_iterator, None)
            if page is not None:
                reports.extend([
                    {
                        'id': report['id'],
                        'name': report['name'],
                        'version': report['version'],
                        'description': ''.join([report['description'][:100], '...' if len(report['description']) > 100 else ''])
                    }
                    for report in page['reports']
                ])
        else:
            page_count = 1
            for page in page_iterator:
                if page_count == page_number:
                    reports.extend([
                        {
                            'id': report['id'],
                            'name': report['name'],
                            'version': report['version'],                            
                            'description': ''.join([report['description'][:100], '...' if len(report['description']) > 100 else ''])
                        }
                        for report in page['reports']
                    ])
                    break
                page_count += 1

            if page_count != page_number:
                print(f"Page {page_number} not found.")

        return json.dumps(reports)

    def get_total_report_pages(self, page_size: int = 15) -> int:
        """
        Get the total number of report pages based on the specified page size.

        Args:
            page_size (int, optional): The number of reports per page. Defaults to 15.

        Returns:
            int: The total number of report pages.
        """
        default_max_results = 15

        if page_size is not None and page_size > default_max_results:
            raise ValueError(f"page_size cannot exceed {default_max_results}")
        
        paginator = self.paginator.paginate(PaginationConfig={'PageSize': page_size})
        total_reports = sum(len(page['reports']) for page in paginator)
        return ceil(total_reports / page_size)

    def _get_term_for_report(self, report_id: str, report_version: int) -> str:
        """
        Get the term token required to download a report.

        Args:
            report_id (str): The ID of the report.
            report_version (int): The version of the report. Some versions of reports are inaccessible if the correct version is not selected. Version 2 is recommended.

        Returns:
            str: The term token for the report.
        """
        response = self.client.get_term_for_report(
            reportId=report_id,
            reportVersion=report_version
        )
        return response['termToken']

    def get_report_url(self, report_id: str, report_version: int) -> str:
        """
        Get the pre-signed URL to download a specific report.

        Args:
            report_id (str): The ID of the report. 
            report_version (int): The version of the report.

        Returns:
            str: The pre-signed URL in JSON format.
        """
        term_token = self._get_term_for_report(report_id, report_version)
        response = self.client.get_report(
            reportId=report_id,
            reportVersion=report_version,
            termToken=term_token
        )
        url = response['documentPresignedUrl']
        return json.dumps({'url': url})

    def search_reports(self, search_keywords: str, max_results: Optional[int] = None) -> List[ReportType]:
        """
        Search for reports based on the provided text.

        Args:
            search_keywords (str): The keywords (i.e. fedramp, cjis) to search for in report names and descriptions.
            max_results (int, optional): The maximum number of results to return.

        Returns:
            List[ReportType]: A list of dictionaries containing the details of the matching reports.
        """
        default_max_results = 10

        if max_results is not None and max_results > default_max_results:
            raise ValueError(f"max_results cannot exceed {default_max_results}")

        paginator = self.paginator.paginate()
        all_reports = [report for page in paginator for report in page['reports']]

        search_words = set(search_keywords.lower().split())
        word_pattern = r'\b{}\b'.format(r'\b|\b'.join(re.escape(word) for word in search_words))

        matching_reports = []
        for report in all_reports:
            name_matches = len(re.findall(word_pattern, report['name'].lower()))
            description_matches = len(re.findall(word_pattern, report['description'].lower()))
            total_matches = name_matches + description_matches
            if total_matches > 0:
                matching_reports.append({
                    'id': report['id'],
                    'name': report['name'],
                    'description': report['description'],
                    'version': report['version'],
                    'match_count': total_matches
                })

        matching_reports.sort(key=lambda x: x['match_count'], reverse=True)

        if max_results is not None:
            matching_reports = matching_reports[:max_results]

        return json.dumps(matching_reports)