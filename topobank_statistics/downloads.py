"""
Place here all download function and register with @register_download_function
"""
import io

import pandas as pd
from django.http import HttpResponse

from topobank.analysis.registry import register_download_function
from topobank.analysis.downloads import publications_urls, analyses_meta_data_dataframe, analysis_header_for_txt_file

from .functions import ART_ROUGHNESS_PARAMETERS


@register_download_function(ART_ROUGHNESS_PARAMETERS, 'results', 'txt')
def download_roughness_parameters_to_txt(request, analyses):
    """Download roughness parameters from given analyses as CSV file.

       Tables with roughness parameters only make sense for analyses
       where subject is a topography (so far). All other analyses
       (e.g. for surfaces) will be ignored here.

        Parameters
        ----------
        request
            HTTPRequest
        analyses
            Sequence of Analysis instances

        Returns
        -------
        HTTPResponse
    """
    # TODO: It would probably be useful to use the (some?) template engine for this.
    # TODO: We need a mechanism for embedding references to papers into output.

    # Only use analyses which are related to a specific topography
    analyses = [a for a in analyses if a.is_topography_related]

    # Collect publication links, if any
    publication_urls = publications_urls(request, analyses)

    # Pack analysis results into a single text file.
    data = []
    f = io.StringIO()
    for i, analysis in enumerate(analyses):
        if i == 0:
            f.write('# {}\n'.format(analysis.function) +
                    '# {}\n'.format('=' * len(str(analysis.function))))

            f.write('# IF YOU USE THIS DATA IN A PUBLICATION, PLEASE CITE XXX.\n' +
                    '#\n')
            if len(publication_urls) > 0:
                f.write('#\n')
                f.write('# For these analyses, published data was used. Please visit these URLs for details:\n')
                for pub_url in publication_urls:
                    f.write(f'# - {pub_url}\n')
                f.write('#\n')

        f.write(analysis_header_for_txt_file(analysis))

        result = analysis.result
        topography = analysis.subject
        for row in result:
            data.append([topography.surface.name,
                         topography.name,
                         row['quantity'],
                         row['direction'] if row['direction'] else '',
                         row['from'] if row['from'] else '',
                         row['symbol'] if row['symbol'] else '',
                         row['value'],
                         row['unit']])

    f.write('# Table of roughness parameters\n')
    df = pd.DataFrame(data, columns=['digital surface twin', 'measurement', 'quantity', 'direction',
                                     'from', 'symbol', 'value', 'unit'])
    df.to_csv(f, index=False)
    f.write('\n')

    # Prepare response object.
    response = HttpResponse(f.getvalue(), content_type='application/text')
    filename = '{}.txt'.format(analysis.function.name.replace(' ', '_'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Close file and return response.
    f.close()
    return response


@register_download_function(ART_ROUGHNESS_PARAMETERS, 'results', 'xlsx')
def download_roughness_parameters_to_xlsx(request, analyses):
    """Download roughness parameters from given analyses as XLSX file.

       Tables with roughness parameters only make sense for analyses
       where subject is a topography (so far). All other analyses
       (e.g. for surfaces) will be ignored here.

        Parameters
        ----------
        request
            HTTPRequest
        analyses
            Sequence of Analysis instances

        Returns
        -------
        HTTPResponse
    """
    analyses = [a for a in analyses if a.is_topography_related]

    f = io.BytesIO()
    excel = pd.ExcelWriter(f)

    data = []
    for analysis in analyses:
        topo = analysis.subject
        for row in analysis.result:
            row['digital surface twin'] = topo.surface.name
            row['measurement'] = topo.name
            data.append(row)

    roughness_df = pd.DataFrame(data, columns=['digital surface twin', 'measurement', 'quantity', 'direction',
                                               'from', 'symbol', 'value', 'unit'])
    roughness_df.replace(r'&Delta;', 'Δ', inplace=True, regex=True)  # we want a real greek delta
    roughness_df.to_excel(excel, sheet_name="Roughness parameters", index=False)
    info_df = analyses_meta_data_dataframe(analyses, request)
    info_df.to_excel(excel, sheet_name='INFORMATION', index=False)
    excel.close()

    # Prepare response object.
    response = HttpResponse(f.getvalue(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = '{}.xlsx'.format(analysis.function.name.replace(' ', '_'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Close file and return response.
    f.close()
    return response

